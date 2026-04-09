"""Allow running the package directly with `python -m stacktrace_lens`."""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
