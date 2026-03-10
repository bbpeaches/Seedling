# traverse-files (scan)

A lightweight, powerful command-line tool to scan directory structures, summarize contents, and export the tree to Markdown, TXT, or Image formats.

## Features
- Generate a visual directory tree with total file/folder counts.
- Export output beautifully to `.md`, `.txt`, or even a rendered `.png` image.
- Control scan depth to avoid overwhelming outputs.
- Easily filter out hidden files or explicitly exclude specific directories (e.g., `node_modules`).
- Automatically saves the report to the parent directory, keeping your target repo clean.

## CLI usage

```bash
# Basic scan (outputs .md file in the target's parent directory)
scan /path/to/dir

# Export as a beautifully rendered image, limiting depth to 2 levels
scan /path/to/dir -f image -d 2

# Exclude heavy folders, show hidden files, and save to desktop
scan /path/to/dir -e node_modules venv -s --outdir ~/Desktop
```

## Example options

* `-f, --format FORMAT`   Output file format (`md`, `txt`, `image`). Default is `md`.
* `-o, --output FILE`     Custom output filename.
* `-s, --show-hidden`     Include hidden files/directories (starting with `.`).
* `-d, --depth DEPTH`     Maximum recursion depth.
* `-e, --exclude LIST`    Files or directories to ignore (e.g., `node_modules`, `.git`).
* `--outdir DIR`          Directory to save the generated file (Default: parent directory).