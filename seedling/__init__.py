"""
Seedling-tools
=============================================
A high-performance CLI toolkit designed for codebase exploration, intelligent analysis, and LLM context aggregation.

Core Capabilities:
1. SCAN: Export directory trees to Markdown, TXT, JSON, or Images.
2. FIND & GREP: Perform exact/fuzzy file searches and regex-based content matching.
3. ANALYZE: Auto-detect project architecture, dependencies, and entry points.
4. SKELETON: Extract Python AST structures (stripping implementation logic).
5. POWER MODE: Aggregate full repository source code for LLM prompts.
6. BUILD: Reconstruct physical file systems from text-based blueprints.

Powered by a unified, single-pass caching traversal engine.

Author: Blue Peach
"""

from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("Seedling-tools")
except PackageNotFoundError:
    __version__ = "dev"
__author__ = "Blue Peach"

# 暴露接口
from .core.config import ScanConfig
from .commands.build.architect import build_structure_from_file

__all__ = [
    "ScanConfig",
    "build_structure_from_file",
    "__version__"
]