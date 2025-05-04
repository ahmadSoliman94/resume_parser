# Installation

This guide will help you set up the Resume Parser AI on your system.

## Prerequisites

Before installing the application, make sure you have the following requirements:

- Python 3.8 or higher
- CUDA-compatible GPU (for optimal performance)
- Docker and Docker Compose (for containerized deployment)
- At least 8GB of RAM (16GB recommended)
- 10GB of free disk space

## Installation Options

### Option 1: Using Docker (Recommended)

The easiest way to get started is using Docker, which handles all dependencies and environment setup automatically.

1. Clone the repository:

```bash
git clone https://github.com/yourusername/resume_parser.git
cd resume_parser
```

2. Start the services using Docker Compose:

```bash
docker-compose up -d
```

3. Verify the installation:

```bash
curl http://localhost:8000/docs
```

The API documentation should now be accessible at [http://localhost:8000/docs](http://localhost:8000/docs).

### Option 2: Manual Installation

If you prefer to install the application manually:

1. Clone the repository:

```bash
git clone https://github.com/yourusername/resume_parser.git
cd resume_parser
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Download the required model:

```bash
mkdir -p app/hf_models
# Download Qwen2.5-VL-7B-Instruct model
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Qwen/Qwen2.5-VL-7B-Instruct', local_dir='app/hf_models/Qwen2.5-VL-7B-Instruct')"
```

5. Start the application:

```bash
python -m app.main
```

The API will be accessible at [http://localhost:8000](http://localhost:8000).

## Configuration

After installation, you may want to customize the application by modifying the `.env` file. See the [Configuration](configuration.md) section for details.

## Troubleshooting Common Installation Issues

### CUDA Issues

If you encounter CUDA-related errors:

1. Verify your NVIDIA drivers are up to date
2. Check CUDA compatibility with installed PyTorch version
3. Try setting the environment variable: `export USE_GPU=False`

### Memory Errors

If you encounter out-of-memory errors:

1. Increase your system swap space
2. Try reducing batch sizes in the configuration
3. Consider using a smaller model or enabling 4-bit quantization

### Port Conflicts

If port 8000 is already in use:

```bash
# For Docker
docker-compose down
# Edit docker-compose.yml to change the port mapping (e.g., "8080:8000")
docker-compose up -d

# For manual installation
python -m app.main --port 8080
```

## Next Steps

After installation, proceed to [Configuration](configuration.md) to customize your setup.