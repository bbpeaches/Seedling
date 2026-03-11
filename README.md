# 🌲 Seedling (v2.0.0)

**Seedling** is a high-performance, 3-in-1 CLI toolkit designed for developers to explore, search, and reconstruct directory structures. Whether you need a beautiful image of your project architecture or a way to spawn a project from a text blueprint, Seedling has you covered.

---

## 🚀 Key Features

* **Scan & Export**: Export directory trees to `Markdown`, `Plain Text`, or high-fidelity `PNG` images with full Chinese character support.
* **Smart Search**: Dual-mode search featuring **Exact Match** and **Fuzzy Suggestions** (powered by Levenshtein distance).
* **Reverse Scaffolding**: Use the `build` command to read any tree diagram and instantly recreate the folder/file hierarchy.
* **Progressive UI**: Dynamic "pulsing" progress bars for scanning and real-time construction animations for building.
* **Interactive Personality**: Built-in session-based "Easter Eggs" that respond to your terminal behavior.

---

## 🛠️ Installation

Seedling is designed to be installed globally via `pipx` for a clean, isolated environment.

### One-Click Setup (Self-Destructing Installers)

Our installers set up the environment, install the tool, and then delete themselves to keep your workspace tidy.

* **Windows**: Run `install.bat`
* **macOS / Linux**: Run `chmod +x install.sh && ./install.sh`

### Developer / Manual Install

If you are modifying the source code, use **Editable Mode**:

```bash
pipx install -e . --force
```

---

## 📖 CLI Reference

### 1. `scan` - The Explorer

Used for scanning directories or searching for items.

| Flag | Short | Description |
| --- | --- | --- |
| `--find` | `-f` | **Search Mode**. Returns exact and fuzzy matches + a saved report. |
| `--format` | `-F` | Output format: `md` (default), `txt`, or `image`. |
| `--depth` | `-d` | Max recursion depth to prevent terminal "walls of text." |
| `--exclude` | `-e` | List of folders to ignore (e.g., `node_modules .git venv`). |
| `--outdir` | `-o` | Where to save the result (Defaults to your current terminal path). |

**Examples:**

```bash
# Export current directory as a PNG image
scan . -F image

# Fuzzy search for a mispelled config file
scan ~/Projects -f "conifg"

# Complex scan: exclude heavy folders, show hidden, save to Desktop
scan . -s -e node_modules -o ~/Desktop -n project_map.md

```

### 2. `build` - The Architect

A dedicated command to turn a text-based tree into a real file system.

**Examples:**

```bash
# Build in current directory using a blueprint
build blueprint.md

# Build a project structure in a specific folder
build structure.txt ~/Desktop/NewApps
```

## 📂 Project Structure

```text
Seedling/
├── pyproject.toml      <- Modern build configuration
├── install.sh/bat      <- Auto-installers
└── scan_tool/
    ├── __init__.py     <- Metadata & versioning
    ├── __main__.py     <- Module entry point
    ├── cli.py          <- Logic for 'scan' and 'build' commands
    ├── scanner.py      <- Search and scanning engine
    ├── builder.py      <- Scaffolding and reverse-build engine
    ├── exporter.py     <- Image rendering & OS-specific fonts
    └── utils.py        <- Session logic, animations, and smart-parsing

```