"""Main CLI entry point that handles direct file arguments."""

import sys
from pathlib import Path

def main():
    """Main CLI function that handles file arguments directly."""
    # If no arguments, show help
    if len(sys.argv) == 1:
        from .cli import cli
        cli(['--help'])
        return

    # If first argument is a file and doesn't look like a subcommand or option
    first_arg = sys.argv[1]
    if not first_arg.startswith('-') and first_arg != 'eval' and first_arg != 'main':
        # Check if it's a file that exists
        if Path(first_arg).exists():
            # Modify sys.argv to add 'main' subcommand
            sys.argv.insert(1, 'main')

    # Import and call the CLI with modified argv
    from .cli import cli
    cli()


if __name__ == "__main__":
    main()