FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy uv configuration and README
COPY pyproject.toml ./
COPY README.md ./

# Copy source code (needed for editable install)
COPY src/ ./src/

# Install uv
RUN pip install uv

# Install dependencies using uv
RUN uv sync

# Copy API code
COPY api/ ./api/

# Create storage directories
RUN mkdir -p /app/storage/uploads /app/storage/workspace /app/storage/outputs

# Expose port
EXPOSE 8002

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8002"]
