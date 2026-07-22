# Use Python 3.11 slim image for small size and compatibility
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY . .

# Copy the outputs folder (model, feature configs)
COPY outputs/ ./outputs/

# Create a .env file placeholder (API keys should be set via environment variables)
RUN touch .env

# Expose port 8000
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
