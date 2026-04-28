#!/usr/bin/env python3
"""DEPRECATED: Use preflight.py instead."""
import os, subprocess, sys
print("⚠️  This script is deprecated. Use preflight.py instead.", file=sys.stderr)
sys.exit(subprocess.call([sys.executable, os.path.join(os.path.dirname(__file__), "preflight.py")] + sys.argv[1:]))
