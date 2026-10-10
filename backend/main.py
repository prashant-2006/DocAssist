from dotenv import load_dotenv
import os
from server import app
import uvicorn

load_dotenv()

def main():
    uvicorn.run(app, host = os.getenv("FASTAPI_HOST"), port = int(os.getenv("FASTAPI_PORT")))
    
if __name__ == "__main__":
    main()