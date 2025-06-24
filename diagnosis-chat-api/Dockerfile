FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY pyproject.toml ./
COPY uv.lock ./
# COPY firebase-adminsdk.json ./

# Install Python dependencies
RUN uv sync
RUN uv pip install -e .

COPY . .

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uv", "run", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
