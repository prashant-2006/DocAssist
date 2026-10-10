from dotenv import load_dotenv
import os
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from openai import OpenAI

load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(
    model = "gemini-embedding-001", 
    google_api_key = os.getenv("GEMINI_API_KEY"), 
    output_dimensionality = 1024
    )

client = OpenAI(
    api_key = os.getenv("GEMINI_API_KEY"),
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
)

def process_query(query: str, session_id: str) -> str:
    vector_store = PineconeVectorStore(
        index_name = os.getenv("PINECONE_INDEX_NAME"), 
        embedding = embeddings, 
        pinecone_api_key = os.getenv("PINECONE_API_KEY"),
        namespace = session_id
    )
    
    context = vector_store.similarity_search(query, k=3)
    context_text = "\n\n".join([doc.page_content for doc in context])

    SYSTEM_PROMPT = f"""You are a helpful assistant that answers questions based on the context provided. 
    Only answer the question based on the context, and if the answer is not contained within the text 
    below, say 'I don't know'.

    Context:
    {context_text}
    """

    client = OpenAI(
        api_key = os.getenv("GEMINI_API_KEY"),
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ]
    )
    
    return response.choices[0].message.content