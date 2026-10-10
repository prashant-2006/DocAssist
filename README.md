# DocAssist: Isolated Parallel RAG Workspace

DocAssist is a high-performance, multi-user Retrieval-Augmented Generation (RAG) application. It allows users to upload PDF documents and chat with an AI assistant specifically grounded in the uploaded context. 

The architecture is built for concurrent multi-user environments. It utilizes Redis queues and background workers to process heavy LLM requests asynchronously, and isolated Pinecone namespaces to ensure complete data privacy between concurrent user sessions. The frontend features an ultra-premium, 60fps glassmorphism UI built with Next.js and Framer Motion.

## 🚀 Features

* **Isolated User Sessions:** Every uploaded PDF is dynamically assigned a unique session ID and embedded into an isolated Pinecone namespace.
* **True Parallel Processing:** Employs RQ (Redis Queue) and multiple background workers to process simultaneous queries from different users without blocking the main API thread.
* **Auto-Teardown:** Ending a session automatically triggers a backend cleanup, purging the user's isolated vector embeddings from the Pinecone database to maintain privacy and save storage.
* **Premium Glassmorphism UI:** Fluid, 60fps animations, intelligent auto-scrolling, and responsive frosted-glass aesthetics.

## 🛠️ Tech Stack

**Frontend:**
* Next.js (App Router)
* Tailwind CSS
* Framer Motion (Animations)
* Lucide React (Iconography)

**Backend:**
* Python & FastAPI
* LangChain & Pinecone (Vector Database)
* Google Generative AI Embeddings (Gemini-embedding-001)
* OpenAI SDK (Routing to Gemini 2.5 Flash)
* Redis & RQ (Task Queuing & Background Workers)

---

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed:
1. **Node.js** (v18+ for Next.js)
2. **Python** (3.10+)
3. **Docker** (to run the Redis server locally)
4. API Keys for **Google Gemini** and **Pinecone**.

---

## 📥 Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/docassist.git](https://github.com/yourusername/docassist.git)
cd docassist
```

### 2. Set Up the Backend Environment
Navigate to the root directory, create a virtual environment, and install the required Python dependencies.

**For Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**For macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in your root folder and add the following variables:
```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=your_pinecone_index_name

# FastAPI Server config
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8000

# Redis/RQ config
RQ_HOST=127.0.0.1
RQ_PORT=6380
```

### 3. Set Up the Frontend Environment
Open a new terminal, navigate to the frontend directory (e.g., `my-app`), and install the Node dependencies:
```bash
cd my-app
npm install
```

---

## 🚀 Running the Application

To run the full stack, you will need multiple terminal windows running simultaneously.

### Step 1: Start Redis
Start a local Redis instance using Docker to handle the task queue. 
```bash
docker run -d -p 127.0.0.1:6380:6379 --name redis-server redis
```
*(If the container is already created, you can simply run `docker start redis-server`).*

### Step 2: Start the FastAPI Server
Open a new terminal, activate your Python virtual environment, and start the backend API.
```bash
python main.py
```
*The backend API will run on http://localhost:8000.*

### Step 3: Start the Next.js Frontend
Open another terminal, navigate to the frontend folder, and start the web app.
```bash
cd my-app
npm run dev
```
*The frontend UI will be accessible at http://localhost:3000.*

---

## ⚡ Single vs. Parallel Chatting (RQ Workers)

DocAssist separates the web server (which receives requests) from the workers (which execute the heavy LangChain/LLM tasks). **To process chats, you must run at least one worker.**

### Single-User Mode
To run the app for personal, sequential use, start **one** worker. Open a new terminal, activate your virtual environment, and run:
```bash
python run_worker.py
```
This single worker will pull jobs from Redis one at a time. If multiple users ask questions simultaneously, the worker will process them sequentially.

### Parallel / Multi-User Mode
To enable true parallel processing where multiple users on your network can upload PDFs and chat simultaneously without waiting in line, simply **spawn multiple workers**. 

Open 2, 3, or more separate terminal windows. In *each* window, activate your virtual environment and run the worker script:
```bash
# Terminal Worker 1
python run_worker.py

# Terminal Worker 2
python run_worker.py

# Terminal Worker 3
python run_worker.py
```
**How it works:** Redis acts as the central dispatcher. When three users ask a question at the exact same time, Redis instantly assigns one job to Worker 1, one to Worker 2, and one to Worker 3. Because Pinecone is segmented by `session_id` namespaces, all three users receive instant, isolated responses simultaneously without cross-talk.
