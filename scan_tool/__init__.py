"""
🌲 Seedling (formerly Directory Tree Scanner)
=============================================
A powerful 3-in-1 CLI toolkit to:
1. SCAN: Export directory structures to MD, TXT, or Images.
2. FIND: Perform exact and fuzzy searches with automated reports.
3. BUILD: Construct real file systems from text-based blueprints.

Author: Blue Peach
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("Seedling")
except PackageNotFoundError:
    __version__ = "dev"

from .cli import main, build_entry
from .scanner import scan_dir_lines, search_items
from .builder import build_structure_from_file

__author__ = "Blue Peach"

__all__ = [
    "main", 
    "build_entry", 
    "scan_dir_lines", 
    "search_items", 
    "build_structure_from_file",
    "__version__"
]