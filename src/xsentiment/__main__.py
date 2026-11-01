"""Module entry point so the CLI is reachable with ``python -m xsentiment``."""
from xsentiment.main import main

if __name__ == "__main__":
    raise SystemExit(main())
