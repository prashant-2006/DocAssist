from rq import SimpleWorker
from client.rq_client import queue  # Import the queue from your client file

if __name__ == '__main__':
    print("🚀 Starting RQ SimpleWorker (Windows Compatible)...")
    
    # Initialize SimpleWorker instead of standard Worker
    worker = SimpleWorker([queue], connection=queue.connection)
    worker.work()