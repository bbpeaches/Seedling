"""Project analyzer for intelligent code analysis."""
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, field
from seedling.core.filesystem import ScanConfig, safe_read_text, is_text_file, is_valid_item
from seedling.core.logger import logger


@dataclass
class ProjectAnalysis:
    """Holds the result of project analysis."""
    project_type: str = "Unknown"
    language: str = "Unknown"
    entry_points: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    architecture: List[str] = field(default_factory=list)
    file_stats: Dict[str, int] = field(default_factory=dict)


# Project type detection signatures
PROJECT_SIGNATURES: Dict[str, Dict] = {
    'python': {
        'files': ['pyproject.toml', 'setup.py', 'requirements.txt', 'setup.cfg', 'Pipfile'],
        'ext': {'.py', '.pyw', '.pyi'}
    },
    'node': {
        'files': ['package.json', 'yarn.lock', 'pnpm-lock.yaml'],
        'ext': {'.js', '.ts', '.jsx', '.tsx', '.mjs', '.cjs'}
    },
    'go': {
        'files': ['go.mod', 'go.sum'],
        'ext': {'.go'}
    },
    'rust': {
        'files': ['Cargo.toml', 'Cargo.lock'],
        'ext': {'.rs'}
    },
    'java': {
        'files': ['pom.xml', 'build.gradle', 'build.gradle.kts'],
        'ext': {'.java', '.kt', '.kts'}
    },
    'cpp': {
        'files': ['CMakeLists.txt', 'Makefile', 'meson.build'],
        'ext': {'.cpp', '.h', '.cc', '.hpp', '.cxx'}
    }
}

# Entry point patterns by language
ENTRY_PATTERNS: Dict[str, List[str]] = {
    'python': [r'if\s+__name__\s*==\s*["\']__main__["\']', r'def\s+main\s*\('],
    'node': [r'export\s+default', r'express\(\)', r'export\s+function', r'app\.listen'],
    'go': [r'func\s+main\s*\(\)'],
    'rust': [r'fn\s+main\s*\(\)'],
    'java': [r'public\s+static\s+void\s+main'],
    'cpp': [r'int\s+main\s*\(']
}


def analyze_project(dir_path: Path, config: ScanConfig) -> ProjectAnalysis:
    """Analyze project structure and detect key characteristics."""
    analysis = ProjectAnalysis()
    analysis.project_type, analysis.language = _detect_type(dir_path)
    analysis.config_files = _find_configs(dir_path, analysis.project_type)
    analysis.entry_points = _find_entries(dir_path, config, analysis.language)
    analysis.dependencies = _extract_deps(dir_path, analysis.project_type)
    analysis.architecture = _detect_arch(dir_path)
    analysis.file_stats = _collect_stats(dir_path, config)
    return analysis


def _detect_type(dir_path: Path) -> Tuple[str, str]:
    """Detect project type based on config files and extensions."""
    detected_types: List[Tuple[str, int]] = []

    for ptype, sig in PROJECT_SIGNATURES.items():
        score = 0
        # Check for config files
        for config_file in sig['files']:
            if dir_path.joinpath(config_file).exists():
                score += 10
        # Check for file extensions
        if 'ext' in sig:
            for ext in sig['ext']:
                count = len(list(dir_path.glob(f"**/*{ext}")))
                score += min(count, 5)  # Cap at 5 to avoid overwhelming
        if score > 0:
            detected_types.append((ptype, score))

    if detected_types:
        # Sort by score, return highest
        detected_types.sort(key=lambda x: x[1], reverse=True)
        best_type = detected_types[0][0]
        return best_type, best_type

    return "generic", "unknown"


def _find_configs(dir_path: Path, ptype: str) -> List[str]:
    """Find configuration files for the detected project type."""
    config_patterns: Dict[str, List[str]] = {
        'python': ['pyproject.toml', 'requirements*.txt', 'setup.py', 'setup.cfg', 'Pipfile'],
        'node': ['package.json', 'tsconfig.json', 'tsconfig.*.json', '.eslintrc*', '.prettierrc*'],
        'go': ['go.mod', 'go.sum'],
        'rust': ['Cargo.toml', 'Cargo.lock'],
        'java': ['pom.xml', 'build.gradle*', 'settings.gradle*'],
        'cpp': ['CMakeLists.txt', 'Makefile', '*.cmake']
    }

    found = []
    for pattern in config_patterns.get(ptype, []):
        matches = [m.name for m in dir_path.glob(pattern) if m.is_file()]
        found.extend(matches)

    return found


def _find_entries(dir_path: Path, config: ScanConfig, lang: str) -> List[str]:
    """Find entry point files based on language patterns."""
    patterns = ENTRY_PATTERNS.get(lang, [])
    if not patterns:
        return []

    entries: List[str] = []
    stack = [dir_path]
    max_entries = 10

    while stack and len(entries) < max_entries:
        curr = stack.pop()
        try:
            for item in curr.iterdir():
                if not is_valid_item(item, dir_path, config):
                    continue
                if item.is_file() and is_text_file(item):
                    content = safe_read_text(item, quiet=True)
                    if content:
                        for p in patterns:
                            if re.search(p, content):
                                entries.append(str(item.relative_to(dir_path)))
                                break
                elif item.is_dir():
                    stack.append(item)
        except PermissionError:
            pass

    return entries


def _extract_deps(dir_path: Path, ptype: str) -> Dict[str, List[str]]:
    """Extract dependencies from project configuration files."""
    deps: Dict[str, List[str]] = {'direct': [], 'dev': []}

    if ptype == 'node':
        pkg = dir_path / 'package.json'
        if pkg.exists():
            try:
                content = safe_read_text(pkg, quiet=True)
                if content:
                    data = json.loads(content)
                    deps['direct'] = list(data.get('dependencies', {}).keys())[:20]
                    deps['dev'] = list(data.get('devDependencies', {}).keys())[:10]
            except (json.JSONDecodeError, Exception):
                pass

    elif ptype == 'python':
        req = dir_path / 'requirements.txt'
        if req.exists():
            try:
                content = safe_read_text(req, quiet=True)
                if content:
                    lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
                    deps['direct'] = [l.split('==')[0].split('>=')[0].split('[')[0] for l in lines[:20]]
            except Exception:
                pass

    elif ptype == 'rust':
        cargo = dir_path / 'Cargo.toml'
        if cargo.exists():
            try:
                content = safe_read_text(cargo, quiet=True)
                if content:
                    # Simple extraction - look for [dependencies] section
                    in_deps = False
                    for line in content.split('\n'):
                        if line.strip() == '[dependencies]':
                            in_deps = True
                            continue
                        if line.strip().startswith('['):
                            in_deps = False
                        if in_deps and '=' in line and not line.strip().startswith('#'):
                            dep_name = line.split('=')[0].strip()
                            if dep_name:
                                deps['direct'].append(dep_name)
            except Exception:
                pass

    return deps


def _detect_arch(dir_path: Path) -> List[str]:
    """Detect architectural patterns based on directory structure."""
    try:
        dirs: Set[str] = {item.name.lower() for item in dir_path.iterdir() if item.is_dir()}
    except PermissionError:
        return []

    hints: List[str] = []

    # MVC pattern
    if {'controllers', 'models', 'views'} & dirs:
        hints.append('MVC')

    # Layered architecture
    if {'services', 'repositories'} & dirs:
        hints.append('Layered')

    # Clean architecture
    if {'domain', 'usecases', 'infrastructure'} & dirs:
        hints.append('Clean')

    # Standard src layout
    if 'src' in dirs and ('tests' in dirs or 'test' in dirs):
        hints.append('SRC-TEST')

    # CI/CD
    if '.github' in dirs or '.gitlab-ci.yml' in {f.name for f in dir_path.iterdir() if f.is_file()}:
        hints.append('CI/CD')

    # Monorepo
    if 'packages' in dirs or 'apps' in dirs:
        hints.append('Monorepo')

    return hints


def _collect_stats(dir_path: Path, config: ScanConfig) -> Dict[str, int]:
    """Collect file extension statistics."""
    stats: Dict[str, int] = {}
    stack = [dir_path]

    while stack:
        curr = stack.pop()
        try:
            for item in curr.iterdir():
                if not is_valid_item(item, dir_path, config):
                    continue
                if item.is_file():
                    ext = item.suffix.lower() or '.no_ext'
                    stats[ext] = stats.get(ext, 0) + 1
                elif item.is_dir():
                    stack.append(item)
        except PermissionError:
            pass

    return stats


def run_analyze(args, target_path: Path):
    """Execute project analysis and output results."""
    config = ScanConfig(
        show_hidden=args.show_hidden,
        excludes=args.exclude,
        quiet=args.quiet
    )

    logger.info(f"\nAnalyzing {target_path}...")

    analysis = analyze_project(target_path, config)

    # Terminal output
    logger.info(f"\n{'='*50}")
    logger.info(f"Project Analysis Results")
    logger.info(f"{'='*50}")
    logger.info(f"  Type: {analysis.project_type}")
    logger.info(f"  Language: {analysis.language}")
    logger.info(f"  Architecture: {', '.join(analysis.architecture) or 'Not detected'}")
    logger.info(f"  Entry Points: {len(analysis.entry_points)}")
    if analysis.entry_points:
        for ep in analysis.entry_points[:5]:
            logger.info(f"    - {ep}")
    logger.info(f"  Config Files: {', '.join(analysis.config_files[:5]) or 'None found'}")
    logger.info(f"  Dependencies: {len(analysis.dependencies.get('direct', []))} direct, "
                f"{len(analysis.dependencies.get('dev', []))} dev")

    # File extension stats summary
    top_exts = sorted(analysis.file_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    if top_exts:
        logger.info(f"  Top Extensions: {', '.join(f'{ext}({cnt})' for ext, cnt in top_exts)}")

    # Output file
    out_dir = Path(args.outdir).resolve() if args.outdir else Path.cwd()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{target_path.name}_analysis.md"

    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(f"# Project Analysis: {target_path.name}\n\n")
        f.write(f"**Type**: {analysis.project_type}\n")
        f.write(f"**Language**: {analysis.language}\n")
        f.write(f"**Path**: `{target_path}`\n\n")

        f.write("## Architecture\n")
        if analysis.architecture:
            for arch in analysis.architecture:
                f.write(f"- {arch}\n")
        else:
            f.write("No architectural patterns detected.\n")

        f.write("\n## Entry Points\n")
        for ep in analysis.entry_points:
            f.write(f"- `{ep}`\n")
        if not analysis.entry_points:
            f.write("No entry points detected.\n")

        f.write("\n## Configuration Files\n")
        for cf in analysis.config_files:
            f.write(f"- `{cf}`\n")

        f.write("\n## Dependencies\n")
        f.write(f"### Direct ({len(analysis.dependencies.get('direct', []))})\n")
        for dep in analysis.dependencies.get('direct', []):
            f.write(f"- {dep}\n")
        f.write(f"\n### Dev ({len(analysis.dependencies.get('dev', []))})\n")
        for dep in analysis.dependencies.get('dev', []):
            f.write(f"- {dep}\n")

        f.write("\n## File Statistics\n")
        for ext, count in sorted(analysis.file_stats.items(), key=lambda x: x[1], reverse=True):
            f.write(f"| `{ext}` | {count} |\n")

    logger.info(f"\nAnalysis saved to: {out_file}")
