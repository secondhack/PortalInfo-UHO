"""Independently check the shipped artifact, not its gzip size."""
from pathlib import Path
import sys

path = Path(__file__).resolve().parent.parent / 'captive-portal/dist/index.html'
size = path.stat().st_size
print(f'{path.name}: {size} bytes / 204800 bytes')
sys.exit(0 if size <= 204800 else 1)
