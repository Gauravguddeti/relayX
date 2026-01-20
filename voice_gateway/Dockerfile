# Voice Gateway Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from voice_gateway directory
COPY voice_gateway/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy voice gateway code
COPY voice_gateway /app

# Copy shared modules
COPY ../shared /app/shared

# Create logs and cache directories
RUN mkdir -p logs .cache

EXPOSE 8001

CMD ["python", "voice_gateway.py"]
