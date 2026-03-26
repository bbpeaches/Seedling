# Seedling-tools

[![Seedling CI](https://img.shields.io/github/actions/workflow/status/bbpeaches/Seedling/ci.yml?branch=main&style=flat-square)](https://github.com/bbpeaches/Seedling/actions)
[![PyPI version](https://img.shields.io/pypi/v/seedling-tools.svg?style=flat-square&color=blue)](https://pypi.org/project/Seedling-tools/)
[![Python Versions](https://img.shields.io/pypi/pyversions/seedling-tools.svg?style=flat-square)](https://pypi.org/project/Seedling-tools/)
[![License](https://img.shields.io/github/license/bbpeaches/Seedling?style=flat-square)](https://github.com/bbpeaches/Seedling/blob/main/LICENSE)

**Seedling-tools** is a high-performance CLI toolkit designed for codebase exploration, intelligent analysis, and LLM context aggregation.

Core Capabilities:
1. SCAN: Export directory trees to Markdown, TXT, JSON, or Images.
2. FIND & GREP: Perform exact/fuzzy file searches and regex-based content matching.
3. ANALYZE: Auto-detect project architecture, dependencies, and entry points.
4. SKELETON: Extract Python AST structures (stripping implementation logic).
5. POWER MODE: Aggregate full repository source code for LLM prompts.
6. BUILD: Reconstruct physical file systems from text-based blueprints.

Powered by a unified, single-pass caching traversal engine.

Read this document in other languages: [简体中文](https://github.com/bbpeaches/Seedling/blob/main/docs/README_zh.md)

---

## Installation

Seedling-tools is designed to be installed globally via `pipx` for a clean, isolated environment.
```
pipx install Seedling-tools
```

### One-Click Setup

* **Windows**: Run `./install.bat`
* **macOS / Linux**: Run `bash install.sh`

### Developer / Manual Install

If you are modifying the source code, use **Editable Mode**:

```bash
pipx install -e . --force
```

---

## Python Library Usage

You can now use Seedling's core features directly in your Python code via the `ScanConfig` engine:

```python
import seedling
from seedling.core.config import ScanConfig
from seedling.core.traversal import traverse_directory, build_tree_lines

# Initialize Configuration
config = ScanConfig(max_depth=2, quiet=True)

# Taking Memory Snapshots
result = traverse_directory("./src", config)

# Render tree lines
lines = build_tree_lines(result, config)
print("\n".join(lines))
```

---

## CLI Reference

Seedling-tools uses a clean, explicit argument system.

### 1. `scan` - The Explorer

Used for scanning directories, extracting code skeletons, or searching for items. Note: `--full` and `--skeleton` are mutually exclusive.

| Argument | Description |
| --- | --- |
| `target` | Target directory for scanning or searching (Defaults to `.`). |
| `--find`, `-f` | **Search Mode**. Fast CLI search (Exact & Fuzzy). Combine with `--full` to export a code report. |
| `--format`, `-F` | Output format: `md` (default), `txt`, `json`, or `image`. |
| `--name`, `-n` | Custom output filename. |
| `--outdir`, `-o` | Where to save the result. |
| `--showhidden` | Include hidden files in the scan. |
| `--depth`, `-d` | Maximum recursion depth. |
| `--exclude`, `-e` | List of items to ignore. **Smart parse: auto-reads `.gitignore` files or accepts globs**. |
| `--include` | **[NEW]** Only include files/directories matching patterns (e.g., `--include "*.py"`). |
| `--type`, `-t` | **[NEW]** Filter by file type: `py`, `js`, `ts`, `cpp`, `go`, `java`, `rs`, `web`, `json`, `yaml`, `md`, `shell`, `all`. |
| `--regex` | **[NEW]** Treat `-f` pattern as regular expression. |
| `--grep`, `-g` | **[NEW]** Search inside file contents (Content Search Mode). |
| `-C`, `--context` | **[NEW]** Show N lines of context around grep matches. |
| `--analyze` | **[NEW]** Analyze project structure, type, dependencies, and architecture. |
| `--full` | **Power Mode**. Appends the full text content of all scanned source files. |
| `--skeleton` | **[Experimental]** AST Code Skeleton extraction. Strips logic, retains signatures. |
| `--text` | **Smart Filter**. Only scan text-based files (ignores binary/media). |
| `--delete` | **Cleanup Mode**. Permanently delete items matched by `--find` (Interactive TTY only). |
| `--dry-run` | **[NEW]** Preview deletions without executing (use with `--delete`). |
| `--verbose` / `-q`| Verbose mode (`-v`) or Quiet mode (`-q`). |

### 2. `build` - The Architect

Turn a text-based tree into a real file system, or restore a project from a snapshot.

| Argument | Description |
| --- | --- |
| `file` | The source tree blueprint file (`.txt` or `.md`). |
| `target` | Where to build the structure (Defaults to current directory). |
| `--direct`, `-d` | **Direct Mode**. Bypass prompts to instantly create a specific path. |
| `--check` | **Dry-Run**. Simulate the build and report missing/existing items. |
| `--force` | **Force Mode**. Overwrite existing files without skipping. |

---

## New in v2.4 - Bug Fixes & Improvements

### Security
- **`--dry-run` Mode**: Preview deletions before executing with `--delete`:
  ```bash
  scan . -f "temp_*" --delete --dry-run
  ```

### Compatibility
- **Python 3.9+ Required for `--skeleton`**: Clear error message for Python 3.8 users
- **Pillow as Optional Dependency**: Install with `pip install Seedling-tools[image]` only if you need image export

### Performance
- **Accurate Memory Calculation**: Fixed memory tracking to prevent OOM crashes on high-Unicode files
- **Conservative Memory Threshold**: Reduced to 80% for additional safety

### JSON Output Mode
Export directory structures as structured JSON for programmatic consumption:
```bash
scan . -F json -o structure.json
```

### File Type & Include Filters
Filter by file type or custom patterns:
```bash
scan . --type py -d 3
scan . --include "*.md" --include "*.txt"
```

### Regex Search Mode
Use regular expressions in search:
```bash
scan . -f "test_.*\.py" --regex
```

### Content Search (Grep Mode)
Search inside file contents with context:
```bash
scan . --grep "TODO" -C 3 --type py
scan . -g "def main" -C 2
```

### Project Analysis
Analyze project structure and dependencies:
```bash
scan . --analyze
```

---

## Project Structure (v2.4)

```text
Seedling/
├── docs/                      # Documentation & Changelogs
│   ├── CHANGELOG.md           # English version history
│   ├── CHANGELOG_zh.md        # Chinese version history
│   └── README_zh.md           # Chinese documentation
├── seedling/                  # Core Package
│   ├── commands/              # CLI Command Routers
│   │   ├── build/             # Build logic (Reverse engineering)
│   │   │   ├── __init__.py    # Build CLI router & validation
│   │   │   └── architect.py   # Blueprint parsing & safe construction
│   │   └── scan/              # Scan logic (Exploration & Extraction)
│   │       ├── __init__.py    # Central Router & Single-pass trigger
│   │       ├── analyzer.py    # Project architecture & dependency analysis
│   │       ├── exclude.py     # .gitignore-style exclusion rule parser
│   │       ├── explorer.py    # Tree rendering & generic format export
│   │       ├── full.py        # Power Mode (LLM context aggregation)
│   │       ├── grep.py        # In-memory content search & context extraction
│   │       ├── json_output.py # Nested JSON structured export
│   │       ├── search.py      # File search (Exact/Fuzzy) & safe deletion
│   │       └── skeleton.py    # Python AST extraction (Implementation stripping)
│   ├── core/                  # Shared Core Engines
│   │   ├── config.py          # Configuration dataclasses & global constants
│   │   ├── detection.py       # File type & binary content probe
│   │   ├── io.py              # File R/W, Fence collision & Overwrite protection
│   │   ├── logger.py          # Centralized CLI formatter & log levels
│   │   ├── patterns.py        # Glob/Regex path matching engine
│   │   ├── sysinfo.py         # Hardware RAM probe & depth limits
│   │   ├── traversal.py       # Unified single-pass caching engine
│   │   └── ui.py              # Interactive prompts & progress bars
│   ├── __init__.py            # Public API & Metadata exposure
│   └── main.py                # CLI Entry Point Router
├── tests/                     # Unit Tests (Core, Edge Cases, IO)
├── install.bat                # Windows one-click installer
├── install.sh                 # Linux/macOS one-click installer
├── LICENSE                    # MIT License
├── pyproject.toml             # Build configuration & Package metadata
├── pytest.ini                 # Pytest configuration file
├── README.md                  # Main documentation
└── test_suite.sh              # Automated E2E tests
```

---

## Changelog

Detailed changes for each release are documented in the [docs/CHANGELOG.md](https://github.com/bbpeaches/Seedling/blob/main/docs/CHANGELOG.md) file.
