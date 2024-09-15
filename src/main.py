import sys
from hoard import Hoard

def main():
    command, is_autocomplete = (
        Hoard()
        .with_config(None)
        .load_trove()
        .start()
    )
    if is_autocomplete:
        print(command.strip(), file=sys.stderr)
    else:
        print(command.strip())

if __name__ == "__main__":
    main()