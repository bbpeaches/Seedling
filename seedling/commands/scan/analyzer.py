import re
import fnmatch
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, field
from seedling.core.config import ScanConfig
from seedling.core.traversal import TraversalResult
from seedling.core.logger import logger
from seedling.core.io import check_overwrite_safely

@dataclass
class ProjectAnalysis:
    """存储分析结果的数据容器"""
    project_type: str = "Unknown"                       # 推断的项目类型
    language: str = "Unknown"                           # 推断的主要编程语言
    entry_points: List[str] = field(default_factory=list) # 检测到的程序入口文件路径列表
    config_files: List[str] = field(default_factory=list) # 发现的关键配置文件列表
    dependencies: Dict[str, List[str]] = field(default_factory=dict) # 提取的依赖包
    architecture: List[str] = field(default_factory=list) # 识别出的架构模式
    file_stats: Dict[str, int] = field(default_factory=dict)         # 各类文件扩展名的数量统计

# 特征签名库
PROJECT_SIGNATURES: Dict[str, Dict] = {
    'python': {'files': ['pyproject.toml', 'setup.py', 'requirements.txt', 'setup.cfg', 'Pipfile'], 'ext': {'.py', '.pyw', '.pyi'}},
    'node': {'files': ['package.json', 'yarn.lock', 'pnpm-lock.yaml'], 'ext': {'.js', '.ts', '.jsx', '.tsx', '.mjs', '.cjs'}},
    'go': {'files': ['go.mod', 'go.sum'], 'ext': {'.go'}},
    'rust': {'files': ['Cargo.toml', 'Cargo.lock'], 'ext': {'.rs'}},
    'java': {'files': ['pom.xml', 'build.gradle', 'build.gradle.kts'], 'ext': {'.java', '.kt', '.kts'}},
    'cpp': {'files': ['CMakeLists.txt', 'Makefile', 'meson.build'], 'ext': {'.cpp', '.h', '.cc', '.hpp', '.cxx'}}
}

# 程序入口特征正则规则库
ENTRY_PATTERNS: Dict[str, List[str]] = {
    'python': [r'if\s+__name__\s*==\s*["\']__main__["\']', r'def\s+main\s*\('],
    'node': [r'export\s+default', r'express\(\)', r'export\s+function', r'app\.listen'],
    'go': [r'func\s+main\s*\(\)'],
    'rust': [r'fn\s+main\s*\(\)'],
    'java': [r'public\s+static\s+void\s+main'],
    'cpp': [r'int\s+main\s*\(']
}

def analyze_project(result: TraversalResult, config: ScanConfig) -> ProjectAnalysis:
    """项目分析"""
    analysis = ProjectAnalysis()
    analysis.project_type, analysis.language = _detect_type(result)
    analysis.config_files = _find_configs(result, analysis.project_type)
    analysis.entry_points = _find_entries(result, analysis.language)
    analysis.dependencies = _extract_deps(result, analysis.project_type)
    analysis.architecture = _detect_arch(result)
    analysis.file_stats = _collect_stats(result)
    return analysis

def _detect_type(result: TraversalResult) -> Tuple[str, str]:
    """对比特征签名库，推断项目类型"""
    detected_types: List[Tuple[str, int]] = []
    for ptype, sig in PROJECT_SIGNATURES.items():
        score = 0
        for config_file in sig['files']:
            if any(item.path.name == config_file and item.depth == 1 for item in result.items):
                score += 10
        if 'ext' in sig:
            for ext in sig['ext']:
                count = sum(1 for item in result.items if not item.is_dir and item.path.suffix.lower() == ext)
                score += min(count, 5)
        if score > 0:
            detected_types.append((ptype, score))
            
    if detected_types:
        detected_types.sort(key=lambda x: x[1], reverse=True)
        return detected_types[0][0], detected_types[0][0]
    return "generic", "unknown"

def _find_configs(result: TraversalResult, ptype: str) -> List[str]:
    """寻找关联的配置文件"""
    config_patterns = {
        'python': ['pyproject.toml', 'requirements*.txt', 'setup.py', 'setup.cfg', 'Pipfile'],
        'node': ['package.json', 'tsconfig.json', 'tsconfig.*.json', '.eslintrc*', '.prettierrc*'],
        'go': ['go.mod', 'go.sum'],
        'rust': ['Cargo.toml', 'Cargo.lock'],
        'java': ['pom.xml', 'build.gradle*', 'settings.gradle*'],
        'cpp': ['CMakeLists.txt', 'Makefile', '*.cmake']
    }
    found = []
    for pattern in config_patterns.get(ptype, []):
        for item in result.items:
            # 限制检索深度为前2层，避免误配子模块配置
            if not item.is_dir and item.depth <= 2 and fnmatch.fnmatch(item.path.name, pattern):
                found.append(item.path.name)
    return list(set(found))

def _find_entries(result: TraversalResult, lang: str) -> List[str]:
    """定位程序入口点"""
    patterns = ENTRY_PATTERNS.get(lang, [])
    if not patterns:
        return []
    entries = []
    for item in result.text_files:
        if len(entries) >= 10:
            break
        content = result.get_content(item, quiet=True)
        if content:
            for p in patterns:
                if re.search(p, content):
                    entries.append(str(item.relative_path))
                    break
    return entries

def _extract_deps(result: TraversalResult, ptype: str) -> Dict[str, List[str]]:
    """特定项目解析浅层配置文件，提取核心依赖列表"""
    deps: Dict[str, List[str]] = {'direct': [], 'dev': []}
    for item in result.text_files:
        if item.depth > 2: 
            continue # 仅关注项目根部或浅层的依赖配置
        
        if ptype == 'node' and item.path.name == 'package.json':
            content = result.get_content(item, quiet=True)
            if content:
                import json
                try:
                    data = json.loads(content)
                    deps['direct'] = list(data.get('dependencies', {}).keys())[:20]
                    deps['dev'] = list(data.get('devDependencies', {}).keys())[:10]
                except Exception:
                    pass
                
        elif ptype == 'python' and item.path.name == 'requirements.txt':
            content = result.get_content(item, quiet=True)
            if content:
                lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
                deps['direct'] = [l.split('==')[0].split('>=')[0].split('[')[0] for l in lines[:20]]
                
        elif ptype == 'rust' and item.path.name == 'Cargo.toml':
            content = result.get_content(item, quiet=True)
            if content:
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
    return deps

def _detect_arch(result: TraversalResult) -> List[str]:
    """猜测项目可能采用的架构模式"""
    dirs = {item.path.name.lower() for item in result.directories if item.depth == 1}
    hints = []
    if {'controllers', 'models', 'views'} & dirs:
        hints.append('MVC')
    if {'services', 'repositories'} & dirs:
        hints.append('Layered')
    if {'domain', 'usecases', 'infrastructure'} & dirs:
        hints.append('Clean')
    if 'src' in dirs and ('tests' in dirs or 'test' in dirs):
        hints.append('SRC-TEST')
    if '.github' in dirs or any(item.path.name == '.gitlab-ci.yml' for item in result.items if item.depth==1):
        hints.append('CI/CD')
    if 'packages' in dirs or 'apps' in dirs:
        hints.append('Monorepo')
    return hints

def _collect_stats(result: TraversalResult) -> Dict[str, int]:
    """对所有扫描到的文件后缀进行聚合计数"""
    stats: Dict[str, int] = {}
    for item in result.items:
        if not item.is_dir:
            ext = item.path.suffix.lower() or '.no_ext'
            stats[ext] = stats.get(ext, 0) + 1
    return stats

def run_analyze(args, target_path: Path, config: ScanConfig, result: TraversalResult):
    """主控函数"""
    analysis = analyze_project(result, config)

    logger.info(f"\n{'='*50}\nProject Analysis Results\n{'='*50}")
    logger.info(f"  Type: {analysis.project_type}")
    logger.info(f"  Language: {analysis.language}")
    logger.info(f"  Architecture: {', '.join(analysis.architecture) or 'Not detected'}")
    logger.info(f"  Entry Points: {len(analysis.entry_points)}")
    for ep in analysis.entry_points[:5]:
        logger.info(f"    - {ep}")
    logger.info(f"  Config Files: {', '.join(analysis.config_files[:5]) or 'None found'}")
    logger.info(f"  Dependencies: {len(analysis.dependencies.get('direct', []))} direct, {len(analysis.dependencies.get('dev', []))} dev")

    top_exts = sorted(analysis.file_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    if top_exts:
        logger.info(f"  Top Extensions: {', '.join(f'{ext}({cnt})' for ext, cnt in top_exts)}")

    out_dir = Path(args.outdir).resolve() if args.outdir else Path.cwd()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{target_path.name}_analysis.md"
    
    if not check_overwrite_safely(out_file):
        return

    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(f"# Project Analysis: {target_path.name}\n\n")
        f.write(f"**Type**: {analysis.project_type}\n**Language**: {analysis.language}\n**Path**: `{target_path}`\n\n")
        
        f.write("## Architecture\n")
        for arch in analysis.architecture:
            f.write(f"- {arch}\n")
        if not analysis.architecture:
            f.write("No architectural patterns detected.\n")
        
        f.write("\n## Entry Points\n")
        for ep in analysis.entry_points:
            f.write(f"- `{ep}`\n")
        
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