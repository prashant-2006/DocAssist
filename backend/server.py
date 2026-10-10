import os
import uuid
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from client.rq_client import queue
from queues.worker import process_query

load_dotenv()

app = FastAPI()

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
async def upload_pdf(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    
    # Save file temporarily to disk for PyPDFLoader
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path)
        docs = loader.load()
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=200)
        chunks = splitter.split_documents(docs)

        # Upload embeddings directly to the user's isolated namespace
        PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            index_name=os.getenv("PINECONE_INDEX_NAME"),
            pinecone_api_key=os.getenv("PINECONE_API_KEY"),
            namespace=session_id,
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {"session_id": session_id, "total_chunks": len(chunks)}

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
    # Wipe all vector embeddings associated with this session's namespace
    try:
        index.delete(delete_all=True, namespace=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete index namespace: {str(e)}")

    return {"status": "success", "message": f"Namespace {session_id} flushed from Pinecone"}