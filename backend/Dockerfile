# Use the official Python image (slim version is smaller/faster)
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (needed for PostgreSQL adapter)
# - libpq-dev: Database adapter
# - tesseract-ocr: The OCR Engine
# - poppler-utils: Helper for converting PDFs to images
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first (for caching layers)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 8000
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]