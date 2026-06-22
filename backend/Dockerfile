FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port (Render sets $PORT automatically, defaulting to 8000 here for documentation)
EXPOSE 8000

# Run the API
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
