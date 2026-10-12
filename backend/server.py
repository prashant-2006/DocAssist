import os
import uuid
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import the expanded suite of LangChain document loaders
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    Docx2txtLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from client.rq_client import queue
from queues.worker import process_query
import redis

load_dotenv()

app = FastAPI()

# Initialize the Redis client
redis_client = redis.Redis(
    host=os.getenv("RQ_HOST", "redis"),
    port=int(os.getenv("RQ_PORT", 6379)),
    decode_responses=True,
)

# Allow Next.js frontend to interact with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    output_dimensionality=1024,
)
pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pinecone_client.Index(os.getenv("PINECONE_INDEX_NAME"))

class ChatRequest(BaseModel):
    session_id: str
    query: str

@app.post("/upload")
async def upload_documents(files: list[UploadFile] = File(...)):
    # 1. Enforce MAX_UPLOAD_FILES constraint from .env
    max_files = int(os.getenv("MAX_UPLOAD_FILES", 5))
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    if len(files) > max_files:
        raise HTTPException(
            status_code=400,
            detail=f"Upload limit exceeded. Maximum allowed is {max_files} files, but received {len(files)}."
        )

    session_id = str(uuid.uuid4())
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
    all_chunks = []
    processed_filenames = []

    # 2. Iterate through each uploaded document
    for file in files:
        file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Route to loader
            if file_extension == "pdf":
                loader = PyPDFLoader(tmp_path)
            elif file_extension in ["txt", "md"]:
                loader = TextLoader(tmp_path, encoding="utf-8")
            elif file_extension == "csv":
                loader = CSVLoader(tmp_path, encoding="utf-8")
            elif file_extension == "docx":
                loader = Docx2txtLoader(tmp_path)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported format for file: {file.filename}")

            docs = loader.load()

            # 3. Explicitly tag original filename and clean metadata before splitting
            for doc in docs:
                doc.metadata["filename"] = file.filename
                doc.metadata["source"] = file.filename  # Overrides temporary disk path

            chunks = splitter.split_documents(docs)
            all_chunks.extend(chunks)
            processed_filenames.append(file.filename)

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    if not all_chunks:
        raise HTTPException(status_code=400, detail="No readable text extracted from uploaded files.")

    # 4. Ingest all chunks across all files into the single isolated session namespace
    PineconeVectorStore.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
        namespace=session_id,
    )

    return {
        "session_id": session_id,
        "total_files": len(processed_filenames),
        "total_chunks": len(all_chunks),
        "filenames": processed_filenames,
    }

@app.post("/chat")
def chat(payload: ChatRequest):
    # Enqueue task with user's isolated session namespace
    job = queue.enqueue(process_query, payload.query, payload.session_id)
    return {"status": "queued", "job_id": job.id}

@app.get("/result/{job_id}")
def get_result(job_id: str):
    job = queue.fetch_job(job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = job.get_status()
    return {
        "status": status,
        "result": job.result if status == "finished" else None,
    }

@app.delete("/session/{session_id}")
def logout_and_cleanup(session_id: str):
    # 1. Wipe all vector embeddings associated with this session's namespace
    try:
        index.delete(delete_all=True, namespace=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete Pinecone namespace: {str(e)}")

    # 2. Wipe the conversational memory associated with this session from Redis
    try:
        redis_client.delete(f"message_store:{session_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete Redis chat history: {str(e)}")

    return {
        "status": "success", 
        "message": f"Session {session_id} completely flushed from Pinecone and Redis"
    }