FROM nvidia/cuda:12.4.0-devel-ubuntu22.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3-setuptools \
    python3-dev \
    build-essential \
    cmake \
    git \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libpq-dev \
    poppler-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv via pip
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir uv 

# Use uv to install torch and other dependencies
RUN uv pip install --system --no-cache-dir torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu121 


RUN pip3 install --no-cache-dir packaging
RUN pip3 install --no-cache-dir flash-attn

# Install from requirements.txt
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt


# Set working directory
WORKDIR /app


# Copy application code
COPY . .

# Initialize EasyOCR and download models
RUN python3 -c "import easyocr; easyocr.Reader(['de', 'en'])"

# Create necessary directories
RUN mkdir -p /app/storage/uploads /app/storage/predictions/extraction_results \
    /app/storage/predictions/logs /app/storage/predictions/annotations

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
