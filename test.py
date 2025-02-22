import shutil
import os

# Clear Hugging Face cache on Windows
cache_path = os.path.join(os.path.expanduser('~'), '.cache', 'huggingface')
if os.path.exists(cache_path):
    shutil.rmtree(cache_path)
    print("Hugging Face cache cleared successfully")

import torch
print("CUDA available:", torch.cuda.is_available())
print("CUDA device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None")