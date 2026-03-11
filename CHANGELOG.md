# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-03-12

### ✨ Added
- **Context Rehydration (Reverse Build)**: The `build` command can now parse `--full` generated markdown files and intelligently inject source code back into the newly created files. 
- **Smart Fallback for Build**: When a blueprint is not found, `build` smoothly prompts to create a direct file or folder instead of crashing.
- **Direct Creation Flag**: Added the `-d` (or `--direct`) flag to bypass prompts and instantly create files or directories.
- **Search Highlighting**: The generated tree document in `find` mode now places a `🎯 [MATCHED]` tag next to matched files.
- **Combo System & Easter Eggs**: Added a time-based combo system for consecutive `scan` commands with hidden terminal animations (Mac/Linux exclusive).

### 🚀 Changed
- **Output Filename**: Removed the redundant `_tree` suffix from default scan outputs (e.g., generates `Seedling.md` instead of `Seedling_tree.md`).
- **Strict User Prompts**: Refactored all `[y/n]` interactions to safely catch invalid keystrokes and prevent accidental pipeline aborts.
- **Root Node Stripping**: The build engine now smartly strips redundant outer wrapper folders from markdown blueprints to ensure perfect path alignment during codebase restoration.

### 🛠 Fixed (修复)
- Fixed an issue where `build` would mistakenly create duplicate files due to path misalignment in source code blocks.
- Resolved permission denial errors on Windows when attempting to write output files to protected system directories.