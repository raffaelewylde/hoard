# Filtering functionality
from typing import List, Dict, Any

def filter_commands(commands: Dict[str, Dict[str, Any]], filter_str: str) -> List[Dict[str, Any]]:
    return [
        {"name": name, **cmd}
        for name, cmd in commands.items()
        if filter_str.lower() in name.lower() or
        any(filter_str.lower() in tag.lower() for tag in cmd["tags"])
    ]