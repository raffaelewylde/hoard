import argparse
import os
import json
import sys
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Optional, Tuple, List, Union, Dict, Any
import logging
from dataclasses import dataclass, field
from config import Config
from filter import filter_commands
from util import ensure_directory, read_json_file, write_json_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class HoardConfig:
    trove_path: Optional[str] = None
    hoard_home: Optional[str] = None
    parameter_token: Optional[str] = None
    config: Optional[Config] = None

@dataclass
class Command:
    name: str
    command: str
    description: str
    tags: List[str] = field(default_factory=list)

class Trove:
    def __init__(self):
        self.commands: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def load_trove_file(cls, path: str):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            trove = cls()
            trove.commands = {k: v for k, v in data.items() if isinstance(v, dict)}
            return trove
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()

    def save_trove_file(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.commands, f, indent=2)

    def add_command(self, name: str, tags: List[str], command: str, description: str):
        self.commands[name] = {
            "tags": tags,
            "command": command,
            "description": description
        }

    def get_command(self, name: str) -> Optional[dict]:
        return self.commands.get(name)

    def remove_command(self, name: str):
        self.commands.pop(name, None)

    def remove_namespace(self, namespace: str):
        self.commands = {k: v for k, v in self.commands.items() if not k.startswith(namespace)}

    def list_commands(self, filter_str: Optional[str] = None, json_output: bool = False, simple_output: bool = False) -> Union[List[dict], str]:
        if filter_str:
            commands = [
                {"name": name, **cmd}
                for name, cmd in self.commands.items()
                if filter_str.lower() in name.lower() or
                any(filter_str.lower() in tag.lower() for tag in cmd["tags"])
            ]
        else:
            commands = [{"name": name, **cmd} for name, cmd in self.commands.items()]

        if json_output:
            return json.dumps(commands, indent=2)
        elif simple_output:
            return "\n".join(cmd["name"] for cmd in commands)
        else:
            return commands

class Hoard:
    def __init__(self):
        self.config = HoardConfig()
        self.trove = Trove()
        self.editor = os.environ.get('EDITOR', 'vim')

    def with_config(self, hoard_home_path: Optional[str] = None) -> 'Hoard':
        if hoard_home_path:
            self.config.hoard_home = hoard_home_path
        else:
            self.config.hoard_home = os.path.join(os.path.expanduser("~"), ".hoard")
        self.config.trove_path = os.path.join(self.config.hoard_home, "trove.json")
        return self

    def load_trove(self) -> 'Hoard':
        if self.config.trove_path:
            self.trove = Trove.load_trove_file(self.config.trove_path)
        self._load_config()
        return self

    def _load_config(self):
        config_path = os.path.join(self.config.hoard_home, "config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.config.parameter_token = config.get('parameter_token')

    def start(self) -> Tuple[str, bool]:
        parser = argparse.ArgumentParser(description="Hoard CLI")
        subparsers = parser.add_subparsers(dest="command")

        info_parser = subparsers.add_parser("info")
        new_parser = subparsers.add_parser("new")
        new_parser.add_argument("name", help="Name of the new command")
        new_parser.add_argument("--tags", nargs="+", help="Tags for the new command")
        new_parser.add_argument("--command", help="The command to store")
        new_parser.add_argument("--description", help="Description of the command")
        list_parser = subparsers.add_parser("list")
        list_parser.add_argument("--filter", help="Filter string for listing commands")
        list_parser.add_argument("--json", action="store_true", help="Output in JSON format")
        list_parser.add_argument("--simple", action="store_true", help="Output in simple format")
        remove_parser = subparsers.add_parser("remove")
        remove_parser.add_argument("name", help="Name of the command to remove")
        remove_namespace_parser = subparsers.add_parser("remove-namespace")
        remove_namespace_parser.add_argument("namespace", help="Namespace to remove")
        pick_parser = subparsers.add_parser("pick")
        pick_parser.add_argument("name", help="Name of the command to pick")
        edit_parser = subparsers.add_parser("edit")
        edit_parser.add_argument("name", help="Name of the command to edit")
        import_parser = subparsers.add_parser("import")
        import_parser.add_argument("path", help="Path to the trove file to import")
        export_parser = subparsers.add_parser("export")
        export_parser.add_argument("path", help="Path to export the trove file")
        shell_config_parser = subparsers.add_parser("shell-config")
        shell_config_parser.add_argument("shell", help="Shell to configure")
        set_parameter_token_parser = subparsers.add_parser("set-parameter-token")
        set_parameter_token_parser.add_argument("token", help="Parameter token to set")

        args = parser.parse_args()

        autocomplete_command = ""
        is_autocomplete = False

        try:
            if args.command == "info":
                self.show_info()
            elif args.command == "new":
                self.new_command(args.name, args.tags, args.command, args.description)
            elif args.command == "list":
                commands = self.list_commands(args.filter, args.json, args.simple)
                print(commands)
            elif args.command == "remove":
                self.remove_command(args.name)
            elif args.command == "remove-namespace":
                self.remove_namespace(args.namespace)
            elif args.command == "pick":
                autocomplete_command = self.pick_command(args.name)
            elif args.command == "edit":
                self.edit_command(args.name)
            elif args.command == "import":
                self.import_trove(args.path)
            elif args.command == "export":
                self.export_command(args.path)
            elif args.command == "shell-config":
                self.shell_config_command(args.shell)
            elif args.command == "set-parameter-token":
                self.set_parameter_token(args.token)
            else:
                parser.print_help()
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")

        return autocomplete_command, is_autocomplete

    def save_trove(self, path: Optional[str] = None):
        path_to_save = path or self.config.trove_path
        if path_to_save:
            self.trove.save_trove_file(path_to_save)

    def show_info(self):
        print(f"Trove path: {self.config.trove_path}")
        print(f"Number of commands: {len(self.trove.commands)}")

    def new_command(self, name: str, tags: List[str], command: str, description: str):
        self.trove.add_command(name, tags, command, description)
        self.save_trove()
        print(f"Added new command: {name}")

    def list_commands(self, filter_str: Optional[str] = None, json_output: bool = False, simple_output: bool = False) -> Union[List[dict], str]:
        return self.trove.list_commands(filter_str, json_output, simple_output)

    def remove_namespace(self, namespace: str):
        self.trove.remove_namespace(namespace)
        self.save_trove()
        print(f"Removed namespace: {namespace}")

    def set_parameter_token(self, token: str):
        self.config.parameter_token = token
        config_path = os.path.join(self.config.hoard_home, "config.json")
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        config['parameter_token'] = token
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Parameter token set: {token}")

    def remove_command(self, name: str):
        if name in self.trove.commands:
            self.trove.remove_command(name)
            self.save_trove()
            print(f"Removed command: {name}")
        else:
            print(f"Command not found: {name}")

    def pick_command(self, name: str) -> str:
        command = self.trove.get_command(name)
        if command:
            return command['command']
        else:
            print(f"Command not found: {name}")
            return ""

    def edit_command(self, name: str):
        command = self.trove.get_command(name)
        if command:
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.tmp') as tf:
                json.dump(command, tf, indent=2)
                tf.flush()
                subprocess.call([self.editor, tf.name])
                tf.seek(0)
                updated_command = json.load(tf)
            self.trove.commands[name] = updated_command
            self.save_trove()
            print(f"Updated command: {name}")
        else:
            print(f"Command not found: {name}")

    def import_trove(self, path: str):
        try:
            with open(path, 'r') as f:
                imported_trove = json.load(f)
            self.trove.commands.update(imported_trove)
            self.save_trove()
            print(f"Imported trove from {path}")
        except FileNotFoundError:
            print(f"File not found: {path}")
        except json.JSONDecodeError:
            print(f"Invalid JSON in file: {path}")

    def export_command(self, path: str):
        try:
            with open(path, 'w') as f:
                json.dump(self.trove.commands, f, indent=2)
            print(f"Exported trove to {path}")
        except IOError:
            print(f"Error writing to file: {path}")

    @staticmethod
    def shell_config_command(shell: str):
        config = {
            "bash": 'eval "$(hoard shell-config bash)"',
            "zsh": 'eval "$(hoard shell-config zsh)"',
            "fish": 'hoard shell-config fish | source',
        }
        if shell in config:
            print(config[shell])
        else:
            print(f"Unsupported shell: {shell}")

# Main function moved to main.py