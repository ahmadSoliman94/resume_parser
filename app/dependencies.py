import os
import sys
from functools import lru_cache

import torch
from transformers import (
    AutoProcessor,
    BitsAndBytesConfig,
    Qwen2_5_VLForConditionalGeneration,
)

from app.core.settings import get_settings

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


@lru_cache
def get_model_and_processor():
    """Load and cache the model and processor."""
    settings = get_settings()

    # Configure quantization
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16
    )

    # Use the pre-downloaded model path in hf_models directory
    model_name = "/app/hf_models/Qwen2.5-VL-7B-Instruct"

    print(f"Loading model from: {model_name}")
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="cuda" if settings.USE_GPU else "cpu",
        local_files_only=True,  # Only use local files
        quantization_config=quant_config,
        attn_implementation="flash_attention_2",
        trust_remote_code=True,
        use_safetensors=True,
    )

    # Load processor
    processor = AutoProcessor.from_pretrained(
        model_name, use_fast=True, local_files_only=True
    )

    return model, processor


def get_autogen_config():
    """Get configuration for AutoGen agents."""
    ollama_base_url = os.environ.get(
        "OLLAMA_BASE_URL", "http://ollama-service:11434/v1"
    )
    return {
        "config_list": [
            {
                "model": "qwen2.5:3b",
                "price": [0.000, 0.000],
                "base_url": ollama_base_url,
                "api_key": "ollama",
            },
        ],
        "cache_seed": None,
    }
