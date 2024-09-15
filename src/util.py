# Utility functions
import os
import json

def ensure_directory(path: str):
    os.makedirs(path, exist_ok=True)

def read_json_file(path: str) -> dict:
    with open(path, 'r') as f:
        return json.load(f)

def write_json_file(path: str, data: dict):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)