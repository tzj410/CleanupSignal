#!/usr/bin/env python3
"""Copy the dependency-free public site into the Sites-supported dist root."""
from pathlib import Path
import shutil
root = Path(__file__).resolve().parents[1]
shutil.copytree(root / 'public', root / 'dist', dirs_exist_ok=True)
print('Static site prepared in dist/')
