from redis import Redis
from rq import Queue
from dotenv import load_dotenv
import os

load_dotenv()

queue = Queue(connection = Redis(
    host = os.getenv("RQ_HOST"),
    port = int(os.getenv("RQ_PORT"))
))