import ast
from pathlib import Path
from seedling.core.logger import logger
from seedling.core.config import ScanConfig
from seedling.core.traversal import TraversalResult
from seedling.core.io import check_overwrite_safely

class SkeletonTransformer(ast.NodeTransformer):
    """AST 节点转换器"""
    
    def _strip_body(self, node):
        """用...替换函数主体"""
        if ast.get_docstring(node):
            node.body = [node.body[0], ast.Expr(value=ast.Constant(value=...))]
        else:
            node.body = [ast.Expr(value=ast.Constant(value=...))]
        return node
        
    def visit_FunctionDef(self, node): 
        return self.generic_visit(self._strip_body(node))
        
    def visit_AsyncFunctionDef(self, node): 
        return self.generic_visit(self._strip_body(node))

def extract_skeleton(code: str) -> str:
    """将 Python 源码解析为抽象语法树"""
    try:
        tree = ast.parse(code)
        transformer = SkeletonTransformer()
        modified_tree = transformer.visit(tree)
        ast.fix_missing_locations(modified_tree) 
        return ast.unparse(modified_tree)
    except Exception as e:
        logger.warning(f"AST Extraction failed: {e}")
        return code

def check_skeleton_support() -> bool:
    """最低要求 Python 3.9"""
    if not hasattr(ast, "unparse"):
        import sys
        logger.error(f"Skeleton extraction requires Python 3.9+ (current: {sys.version_info.major}.{sys.version_info.minor})")
        return False
    return True

def run_skeleton(args, target_path: Path, config: ScanConfig, result: TraversalResult):
    """主控逻辑"""
    logger.info(f"Extracting Python code structure from {target_path}...")
    
    if args.outdir:
        out_dir_path = Path(args.outdir).resolve()
    else:
        out_dir_path = Path.cwd()
        
    out_dir_path.mkdir(parents=True, exist_ok=True)
    
    if args.name:
        out_name = args.name
    else:
        if target_path.name:
            root_label = target_path.name
        else:
            root_label = 'root'
        out_name = f"{root_label}_skeleton.md"
        
    final_file = out_dir_path / out_name

    if not check_overwrite_safely(final_file): 
        return 

    sections = ["\n\n" + "="*60, "🦴 PROJECT CODE SKELETON", "="*60 + "\n"]
    py_files_processed = 0

    for item in result.text_files:
        if item.path.suffix.lower() == '.py':
            content = result.get_content(item, quiet=True)
            if content:
                skeleton_code = extract_skeleton(content)
                sections.append(f"### FILE: {item.relative_path}")
                sections.append(f"```python\n{skeleton_code}\n```\n")
                py_files_processed += 1

    if py_files_processed == 0:
        logger.warning("🚫 No valid Python (.py) files found in the target directory.")
        return

    try:
        with open(final_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(sections))
        logger.info(f"✅ Successfully extracted skeleton from {py_files_processed} Python files.")
        logger.info(f"🎉 SUCCESS! Skeleton file saved to:\n   👉 {final_file}\n")
    except Exception as e:
        logger.error(f"Failed to save file: {e}")