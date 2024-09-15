# CLI commands implementation
from typing import List, Optional
from hoard import Hoard

def handle_info(hoard: Hoard):
    hoard.show_info()

def handle_new(hoard: Hoard, name: str, tags: List[str], command: str, description: str):
    hoard.new_command(name, tags, command, description)

def handle_list(hoard: Hoard, filter_str: Optional[str], json_output: bool, simple_output: bool):
    return hoard.list_commands(filter_str, json_output, simple_output)

def handle_remove(hoard: Hoard, name: str):
    hoard.remove_command(name)

def handle_remove_namespace(hoard: Hoard, namespace: str):
    hoard.remove_namespace(namespace)

def handle_pick(hoard: Hoard, name: str) -> str:
    return hoard.pick_command(name)

def handle_edit(hoard: Hoard, name: str):
    hoard.edit_command(name)

def handle_import(hoard: Hoard, path: str):
    hoard.import_trove(path)

def handle_export(hoard: Hoard, path: str):
    hoard.export_command(path)

def handle_shell_config(shell: str):
    return Hoard.shell_config_command(shell)

def handle_set_parameter_token(hoard: Hoard, token: str):
    hoard.set_parameter_token(token)