# Lightweight CPU container for Render
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY kobo_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and model files
COPY kobo_service/app.py /app/app.py
COPY models/elasmobranch_mobilenet.onnx /app/models/elasmobranch_mobilenet.onnx
COPY models/metadata.json /app/models/metadata.json

ENV PORT=10000
EXPOSE 10000

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000}"]
