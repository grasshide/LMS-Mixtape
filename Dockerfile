FROM python:3.14-slim

# Install system dependencies
RUN apt-get update && apt-get install -y sqlite3 zlib1g-dev libjpeg-dev gcc ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /exports

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"] 