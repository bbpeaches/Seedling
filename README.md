# 🌲 Seedling (v2.2.1)

[![Seedling CI](https://img.shields.io/github/actions/workflow/status/bbpeaches/Seedling/ci.yml?branch=main&style=flat-square)](https://github.com/bbpeaches/Seedling/actions)
[![PyPI version](https://img.shields.io/pypi/v/seedling-tools.svg?style=flat-square&color=blue)](https://pypi.org/project/Seedling-tools/)
[![Python Versions](https://img.shields.io/pypi/pyversions/seedling-tools.svg?style=flat-square)](https://pypi.org/project/Seedling-tools/)
[![License](https://img.shields.io/github/license/bbpeaches/Seedling?style=flat-square)](https://github.com/bbpeaches/Seedling/blob/main/LICENSE)

**Seedling** is a high-performance, 3-in-1 CLI toolkit designed for developers to explore, search, and reconstruct directory structures. Whether you need a beautiful image of your project architecture or a way to spawn a project from a text blueprint, Seedling has you covered.

---

## 🚀 Key Features

* **Modular Architecture**: A completely rebuilt core engine, separating commands and core logic for infinite scaling and professional maintenance.
* **Public Python API (Quiet Mode) [NEW]**: Seedling is now a library! You can `import seedling` in your scripts to use its powerful scanning and building engines programmatically, now with a silent `quiet=True` mode for clean server logs.
* **Context Rehydration 🌟**: Generate a project snapshot using `scan --full`, and use `build` to flawlessly restore the *entire* directory structure along with the original source code.
* **Smart Text Filter (`--text`)**: Strictly ignore binary and media files during tree scanning and searching. Intelligently whitelists extension-less files (Makefile, Dockerfile) and hidden dotfiles.
* **C++/CUDA Ecosystem Support [NEW]**: Deeply integrated support for low-level system files (`.cc`, `.cxx`, `.hpp`, `.cu`, `.cuh`, `.cs`) ensuring zero code loss during context aggregation.
* **Dangerous Deletion (`--delete`)**: Search for files or folders and permanently wipe them out with a built-in safety lock.
* **Scan & Export**: Export directory trees to `Markdown`, `Plain Text`, or high-fidelity `PNG` images with full Chinese character support and automatic trailing slashes for directories.
* **Reverse Scaffolding**: Use the `build` command to read any tree diagram (even those copied from a README) and instantly recreate the folder/file hierarchy.

---

## 🛠️ Installation

Seedling is designed to be installed globally via `pipx` for a clean, isolated environment.

### One-Click Setup

* **Windows**: Run `./install.bat`
* **macOS / Linux**: Run `bash install.sh`

### Developer / Manual Install

If you are modifying the source code, use **Editable Mode**:

```bash
pipx install -e . --force
```

---

## 🐍 Python Library Usage

You can now use Seedling's core features directly in your Python code:

```python
import seedling

# Generate directory tree lines (Use quiet=True to suppress CLI output)
lines = seedling.scan_dir_lines("./src", max_depth=2, quiet=True)
print("\n".join(lines))

# Search for specific items
exact, fuzzy = seedling.search_items(".", keyword="utils", quiet=True)

# Reconstruct a project from a blueprint
seedling.build_structure_from_file("blueprint.md", "./new_project")
```

---

## 📖 CLI Reference

Seedling 2.2.1 uses a clean, explicit argument system. All ambiguous short flags have been removed to ensure readability.

### 1. `scan` - The Explorer

Used for scanning directories or searching for items.

| Argument | Description |
| --- | --- |
| `target` | Target directory for scanning or searching (Defaults to `.`). |
| `--version` | Show program's version number and exit. |
| `--find` | **Search Mode**. Returns exact and fuzzy matches + a saved report. |
| `--format` | Output format: `md` (default), `txt`, or `image`. |
| `--name` | Custom output filename. |
| `--outdir` | Where to save the result. |
| `--show-hidden` | Include hidden files in the scan. |
| `--depth` | Maximum recursion depth. |
| `--exclude` | List of files/directories to ignore. |
| `--full` | **Power Mode**. Appends the full text content of all scanned source files. |
| `--text` | **Smart Filter**. Only scan text-based files (ignores binary/media). |
| `--delete` | **Cleanup Mode**. Permanently delete items matched by `--find`. |

### 2. `build` - The Architect

Turn a text-based tree into a real file system, or restore a project from a snapshot.

| Argument | Description |
| --- | --- |
| `file` | The source tree blueprint file (`.txt` or `.md`). |
| `target` | Where to build the structure (Defaults to current directory). |
| `--version` | Show program's version number and exit. |
| `--direct` | **Direct Mode**. Bypass prompts to instantly create a specific path. |
| `--check` | **Dry-Run**. Simulate the build and report missing/existing items. |
| `--force` | **Force Mode**. Overwrite existing files without skipping. |

---

## 📂 Project Structure (v2.2.1)

```text
Seedling/
├── seedling/                  # Core Package
│   ├── commands/              # CLI Command Routers
│   │   ├── scan/              # Scan logic (explorer, search, full)
│   │   └── build/             # Build logic (architect)
│   ├── core/                  # Shared Engines
│   │   ├── ui.py              # Animations & Progress bars
│   │   ├── io.py              # File R/W & Image rendering
│   │   └── filesystem.py      # Traversal & Text verification
│   ├── __init__.py            # Public API & Metadata
│   └── main.py                # Entry Point Router
├── pyproject.toml             # Build configuration
├── install.sh/bat             # One-click installers
└── test_suite.sh              # Ultimate E2E tests
```

---

## 🛡️ Stability & Hardening

Seedling is built to be unbreakable. It includes:

* **Path Traversal Prevention [NEW]**: Strict `.is_relative_to()` boundary checks during build operations to completely prevent zero-day directory escape attacks.
* **Memory Protection**: Automatically skips files larger than 2MB during `--full` scans to prevent crashes.
* **Graceful Interruptions**: `Ctrl+C` safe. It saves your progress even if you stop a scan midway.
* **Symlink Loop Defense**: Detects and ignores infinite directory loops.
* **Terminal Safety**: Built-in UTF-8 encodings to prevent Windows terminal startup crashes.

---

## 📜 Changelog

Detailed changes for each release are documented in the [CHANGELOG.md](https://www.google.com/search?q=./CHANGELOG.md) file.

### Latest Update: v2.2.1 (The Sentinel Patch)

* **Security Hotfix**: Patched a critical Path Traversal vulnerability in the build engine.
* **Windows Fix**: Resolved a fatal `NameError` startup crash affecting Windows users.
* **API Quiet Mode**: Added `quiet=True` support for clean library integration without CLI pollution.
* **Expanded Ecosystem**: Full context aggregation support for C/C++, CUDA, and C# files.
* **Search Robustness**: Fixed a severe fuzzy search bug where identically named files would overwrite each other in the index.
