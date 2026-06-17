"""
gitlytics/__main__.py
Makes `python -m gitlytics` work identically to the `gitlytics` console command.
This is the entry point Python calls when the package is run with -m.
"""
from gitlytics.cli import main

# Run the CLI when invoked as `python -m gitlytics`
main()
