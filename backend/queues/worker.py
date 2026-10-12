from dotenv import load_dotenv
import os
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from openai import OpenAI
from langchain_community.chat_message_histories import RedisChatMessageHistory

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
    
    # Connect to redis for history
    redis_url = f"redis://{os.getenv('RQ_HOST', 'redis')}:{os.getenv('RQ_PORT', 6379)}/0"
    history = RedisChatMessageHistory(session_id = session_id, url = redis_url)
    
    # Slice history
    window_size = int(os.getenv("CHAT_MEMORY_WINDOW", 3))
    message_limit = window_size * 2
    past_messages = history.messages[-message_limit:] if window_size > 0 else []
    
    # Convert history to OpenAI format
    formatted_history = []
    for msg in past_messages:
        role = "user" if msg.type == "human" else "assistant"
        formatted_history.append({"role": role, "content": msg.content})
    
    context = vector_store.similarity_search(query, k=4)
    
    formatted_contexts = []
    for doc in context:
        # Extract both filename and page number from metadata
        filename = doc.metadata.get("filename") or doc.metadata.get("source", "Unknown Document")
        page_num = doc.metadata.get("page")
        
        # Format the label based on whether page numbers exist
        if page_num is not None:
            source_label = f"{filename} | Page {int(page_num) + 1}"
        else:
            source_label = f"{filename}"
            
        formatted_contexts.append(f"--- Source: {source_label} ---\n{doc.page_content}")

    context_text = "\n\n".join(formatted_contexts)

    SYSTEM_PROMPT = f"""You are DocAssist, a helpful document analysis assistant. 
    
    You have two jobs:
    1. Be polite, conversational, and remember details the user tells you about themselves in the chat history.
    2. When answering factual questions about the uploaded documents, use ONLY the context provided below. If the documents do not contain the answer, say 'I don't know'.
    
    IMPORTANT RULE: Whenever you extract facts from the context below, you MUST append a citation at the very end of your response indicating exactly which file and page you found it in.
    Example format: "This is the answer. (Source: financial_report.pdf, Page 4)"

    Context from document:
    {context_text}
    """
    
    # Add system prompt, message history and query for message sequence
    messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages_payload.extend(formatted_history)
    messages_payload.append({"role": "user", "content": query})

    response = client.chat.completions.create(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        messages=messages_payload
    )
    
    # Save history
    answer = response.choices[0].message.content
    history.add_user_message(query)
    history.add_ai_message(answer)
    
    return answer