# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy ONLY what's needed
COPY requirements_minimal.txt .
COPY src/ ./src/

# Install only essential dependencies
RUN pip install --no-cache-dir fastapi uvicorn pymongo kafka-python requests

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]