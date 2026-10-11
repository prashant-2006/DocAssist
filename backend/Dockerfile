# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# The command is left blank here because docker-compose will 
# specify whether this container runs the API or a Worker.