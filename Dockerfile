
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (if any needed for compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Expose API and Streamlit ports
EXPOSE 8000
EXPOSE 8501

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
