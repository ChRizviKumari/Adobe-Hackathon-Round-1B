# Use Python 3.9 slim image
FROM --platform=linux/amd64 python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download and cache NLTK & spaCy data during build (offline-ready)
RUN python -m nltk.downloader punkt stopwords && \
    python -m spacy download en_core_web_sm

# Copy app files
COPY . .

# Run your analyzer script (change if your main script has a different name)
CMD ["python", "main.py"]
