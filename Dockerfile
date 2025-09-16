# Use slim Python base for small image size
FROM python:3.12-slim AS base

# Install system dependencies (minimal). Pandas wheels work on slim without extra deps.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install dependencies first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project sources
COPY app /app/app
COPY main.py README.md pyproject.toml /app/

# Create a non-root user
RUN useradd -m appuser
USER appuser

# Expose the default port
EXPOSE 8000

# Start the FastAPI app
# Note: GEMINI_API_KEY must be provided via environment variable
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
