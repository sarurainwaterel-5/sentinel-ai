import os
from pathlib import Path
root = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HOME", str(root / ".local/huggingface"))
from huggingface_hub import snapshot_download
snapshot_download("sentence-transformers/all-MiniLM-L6-v2", ignore_patterns=["onnx/*", "openvino/*", "*.h5", "rust_model.ot", "pytorch_model.bin"])
print("Embedding model cached.")
