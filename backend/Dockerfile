# Use official Playwright image which includes all browser dependencies
# We use jammy (Ubuntu 22.04) as base
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app

# Install uv for package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install dependencies including the project itself
# --frozen ensures we use the exact versions in uv.lock
RUN uv sync --frozen --no-cache

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 8000

# Start the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
