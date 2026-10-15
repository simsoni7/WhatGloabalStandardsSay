"""Compatibility entry point: the active library is now the source-backed graph."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('build_knowledge.py')),run_name='__main__')
