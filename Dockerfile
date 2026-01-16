# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance directory (fallback if volume not mounted)
RUN mkdir -p instance

# Make start script executable
RUN chmod +x start.sh

# Expose port (Railway sets PORT env var)
EXPOSE 8080

# Run the startup script
CMD ["./start.sh"]
