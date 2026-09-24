"""Compatibility entry point; install the project first with pip install -e ."""
from gestureos.capture import main

if __name__ == "__main__":
    raise SystemExit(main())
