"""
LightDB CLI
"""

from . import installer
from . import init
from . import interface

import sys

if __name__ == "__main__":
    interface.verify_args(sys.argv[1:])
    interface.run_cli(sys.argv[1:])
else:
    print("LightDB CLI is meant to be run as a script, not loaded as a module.")