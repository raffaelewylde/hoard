# Configuration management
import os
import json
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    hoard_home: str
    trove_path: str
    parameter_token: Optional[str] = None

def load_config() -> Config:
    home = os.path.expanduser("~")
    hoard_home = os.path.join(home, ".hoard")
    trove_path = os.path.join(hoard_home, "trove.json")
    config_path = os.path.join(hoard_home, "config.json")

    config = Config(hoard_home=hoard_home, trove_path=trove_path)

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = json.load(f)
            config.parameter_token = data.get('parameter_token')

    return config

def save_config(config: Config):
    config_path = os.path.join(config.hoard_home, "config.json")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump({"parameter_token": config.parameter_token}, f, indent=2)