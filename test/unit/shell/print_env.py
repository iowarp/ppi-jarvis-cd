#!/usr/bin/env python3
"""
Simple script to print environment variables.
Usage: print_env.py VAR1 VAR2 VAR3 ...
"""
import sys
import os

if len(sys.argv) < 2:
    print("Usage: print_env.py VAR1 [VAR2 ...]", file=sys.stderr)
    sys.exit(1)

for var_name in sys.argv[1:]:
    value = os.environ.get(var_name)
    if value is not None:
        print(f"{var_name}={value}")
    else:
        print(f"ERROR: {var_name} not found", file=sys.stderr)
        sys.exit(1)

sys.exit(0)
