from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
import os
from langchain_pinecone import PineconeVectorStore

load_dotenv()

# Load
file_path = "./data/os.pdf"
print(f"📂 Loading PDF: {file_path}")

loader = PyPDFLoader(file_path)
docs = loader.load()
print(f"✅ PDF loaded successfully!")
print(f"📄 Total pages loaded: {len(docs)}")

# Split
print("\n✂ Splitting PDF into chunks...")
text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 200)
chunks = text_splitter.split_documents(documents = docs)
print(f"✅ Text splitting completed!")
print(f"🧩 Total chunks created: {len(chunks)}")

# Vector Embedding
embeddings = GoogleGenerativeAIEmbeddings(
    model = "gemini-embedding-001", 
    google_api_key = os.getenv("GEMINI_API_KEY"), 
    output_dimensionality = 1024
)
print("✅ Gemini embeddings initialized!")

# Store in Pinecone
print(f"\n🔌 Connecting to Pinecone index: {os.getenv('PINECONE_INDEX_NAME')}")
vector_store = PineconeVectorStore( 
    index_name = os.getenv("PINECONE_INDEX_NAME"), 
    embedding = embeddings, 
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
)
print("✅ Connected to Pinecone!")
print("\n📤 Generating embeddings and uploading chunks to Pinecone...")

vector_store.delete(delete_all = True)
vector_store.add_documents(chunks)

print("🎉 All chunks uploaded successfully!")
print(f"📦 Total chunks stored: {len(chunks)}")