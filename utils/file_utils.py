import os
import json

# Use /mnt/data if running in Docker with persistent disk
if os.path.exists("/mnt/data"):
    BASE_DATA_DIR = "/mnt/data"
else:
    # Default to local `data/` directory
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BASE_DATA_DIR = os.path.join(PROJECT_ROOT, "data")

def load_json(filename):
    path = os.path.join(BASE_DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json(filename, data):
    path = os.path.join(BASE_DATA_DIR, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
