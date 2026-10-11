# DocAssist: Isolated Parallel RAG Workspace

DocAssist is a high-performance, multi-user Retrieval-Augmented Generation (RAG) application. It allows users to upload various documents (PDF, DOCX, TXT, MD, CSV) and chat with an AI assistant specifically grounded in the uploaded context. 

The architecture is built for concurrent multi-user environments. It utilizes Redis queues and background workers to process heavy LLM requests asynchronously, and isolated Pinecone namespaces to ensure complete data privacy between concurrent user sessions. The frontend features an ultra-premium, 60fps glassmorphism UI built with Next.js and Framer Motion.

## 🚀 Features

- **Multi-Format Support:** Ingests PDF, DOCX, TXT, Markdown, and CSV files dynamically.
- **Isolated User Sessions:** Every uploaded document is assigned a unique session ID and embedded into an isolated Pinecone namespace.
- **Stateful Conversational Memory:** Maintains chat history context across stateless parallel workers using Redis. Employs a sliding memory window so the AI remembers previous questions and answers during your active session.
- **True Parallel Processing:** Employs RQ (Redis Queue) and multiple background workers to process simultaneous queries from different users without blocking the main API thread.
- **Auto-Teardown:** Ending a session automatically triggers a backend cleanup, purging the user's isolated vector embeddings from Pinecone and wiping the chat history from Redis to maintain privacy and save storage.
- **Premium Glassmorphism UI:** Fluid, 60fps animations, intelligent auto-scrolling, beautiful markdown rendering, and responsive frosted-glass aesthetics.

## 🛠️ Tech Stack

**Frontend:**
- Next.js (App Router, Node 20+)
- Tailwind CSS v4 & Typography Plugin
- Framer Motion & Lucide React

**Backend:**
- Python 3.11 & FastAPI
- LangChain & Pinecone (Vector Database)
- Google Generative AI Embeddings (Gemini-embedding-001)
- OpenAI SDK (Routing to Gemini 3.5 Flash-Lite)
- Redis & RQ (Task Queuing, Background Workers, & Session Memory)
- Docker Compose (Container Orchestration)

---

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed:
1. **Docker Desktop** (Engine running)
2. **Node.js** (v20+) *— only required for fallback manual mode*
3. **Python** (v3.11+) *— only required for fallback manual mode*
4. API Keys for **Google Gemini** and **Pinecone**.

---

## 📥 Installation & Environment Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/docassist.git](https://github.com/yourusername/docassist.git)
cd docassist
```

### 2. Configure Environment Variables
Create a `.env` file in your **root folder** (alongside `docker-compose.yml`) and add the following variables:

```env
# AI & Vector DB API Keys
GEMINI_API_KEY=your_gemini_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=your_pinecone_index_name

# FastAPI Server config
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# Redis/RQ config
# Note: Keep RQ_HOST=redis if using Docker. Change to 127.0.0.1 if running manually.
RQ_HOST=redis
RQ_PORT=6379

# Chat Memory Config
# Defines how many past user-AI interactions the bot remembers for context
CHAT_MEMORY_WINDOW=3
```

> **🧠 How Memory Configuration Works:**
> The `CHAT_MEMORY_WINDOW` defines the sliding window of conversational memory. A value of `3` means the AI will remember the last 3 questions you asked and its last 3 answers (6 messages total). This prevents context-window token overflow while keeping the AI aware of the current conversation thread.

---

## 🚀 Method 1: Docker Compose (Recommended)

The easiest and most robust way to run DocAssist is via Docker Compose. This single command builds the Next.js frontend, the FastAPI server, the Redis broker, and dynamically spins up isolated, parallel background workers.

Open a single terminal in the root folder and run:
```bash
docker compose up --build --scale worker=3
```
- **Frontend UI:** Available at `http://localhost:3000`
- **Backend API:** Available at `http://localhost:8000`
- **Parallelism:** The `--scale worker=3` flag spawns three identical containerized workers that listen to the Redis queue simultaneously. 

To shut down the architecture cleanly (without corrupting container data), press `Ctrl+C` once, then run `docker compose down`.

---

## ⚠️ Method 2: Manual Setup (Fallback / Dev Mode)

If Docker fails abruptly or you wish to develop locally without containers, use this manual multi-terminal fallback method. 

*Before starting, change `RQ_HOST=redis` to `RQ_HOST=127.0.0.1` and `RQ_PORT=6379` to `RQ_PORT=6380` in your `.env` file.*

### Step 1: Start Redis
Start a local Redis instance mapped to port 6380.
```bash
docker run -d -p 127.0.0.1:6380:6379 --name redis-server redis
```

### Step 2: Start the FastAPI Server
Open a terminal, create a virtual environment, install dependencies, and start the API.
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Step 3: Start the Next.js Frontend
Open a second terminal, navigate to the frontend folder, install packages, and run the app.
```bash
cd my-app
npm install
npm run dev
```

### Step 4: Spawn Workers for Parallel Chatting
The web server only receives requests. To process them, you must start worker processes. Open new terminal windows, activate the Python virtual environment in each, and run:
```bash
# Terminal 3 (Worker 1)
cd backend && .\.venv\Scripts\activate && python run_worker.py

# Terminal 4 (Worker 2 - Optional, for parallel multi-user testing)
cd backend && .\.venv\Scripts\activate && python run_worker.py
```