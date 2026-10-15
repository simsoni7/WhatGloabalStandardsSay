"""Compatibility entry point for the rebuilt UI browser workflows."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
raise SystemExit(subprocess.run([sys.executable,str(ROOT/'tests/browser_library.py')],cwd=ROOT).returncode)
