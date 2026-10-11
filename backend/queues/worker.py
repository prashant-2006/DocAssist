from dotenv import load_dotenv
import os
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from openai import OpenAI
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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
    redis_url = f"redis://{os.getenv('RQ_HOST')}:{os.getenv('RQ_PORT')}/0"
    history = RedisChatMessageHistory(session_id = session_id, url = redis_url)
    
    # Slice history
    window_size = int(os.getenv("CHAT_MEMORY_WINDOW", 3))
    message_limit = window_size * 2
    past_messages = history.messages[-message_limit:] if window_size > 0 else []
    
    # Convert history to OpenAI format
    formatted_history = []
    for msg in past_messages:
        if msg.type == "human":
            role = "user"
        else:
            role = "assistant"
        formatted_history.append({"role": role, "content": msg.content})
    
    context = vector_store.similarity_search(query, k=3)
    context_text = "\n\n".join([doc.page_content for doc in context])

    SYSTEM_PROMPT = f"""You are DocAssist, a helpful document analysis assistant. 
    
    You have two jobs:
    1. Be polite, conversational, and remember details the user tells you about themselves in the chat history.
    2. When answering factual questions about the uploaded document, use ONLY the context provided below. If the document does not contain the answer to a factual question, say 'I don't know'.

    Context from document:
    {context_text}
    """
    
    # Add system prompt, message history and query for message sequence
    messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages_payload.extend(formatted_history)
    messages_payload.append({"role": "user", "content": query})

    client = OpenAI(
        api_key = os.getenv("GEMINI_API_KEY"),
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    response = client.chat.completions.create(
        model="gemini-3.8-flash",
        messages=messages_payload
    )
    
    # Save history
    answer = response.choices[0].message.content
    history.add_user_message(query)
    history.add_ai_message(answer)
    
    return answer