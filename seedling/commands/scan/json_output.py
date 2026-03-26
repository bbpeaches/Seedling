import json
from pathlib import Path
from typing import Dict, Any
from seedling.core.config import ScanConfig
from seedling.core.traversal import TraversalResult

def build_json_structure(dir_path: Path, config: ScanConfig, result: TraversalResult) -> Dict[str, Any]:
    """构建嵌套的 JSON 目录树"""
    items_by_parent = {}
    for item in result.items:
        items_by_parent.setdefault(item.path.parent, []).append(item)

    def _build_node(current_path: Path, is_dir: bool) -> Dict[str, Any]:
        """递归拼接单个文件或目录"""
        
        node: Dict[str, Any] = {
            "name": current_path.name,
            "type": "directory" if is_dir else "file",
            "path": str(current_path.relative_to(dir_path)) if current_path != dir_path else "."
        }
        
        if not is_dir:
            node["extension"] = current_path.suffix.lower() or None
        else:
            children = []
            if current_path in items_by_parent:
                # 目录优先，同级按名称字母顺序排列
                sorted_children = sorted(items_by_parent[current_path], key=lambda x: (not x.is_dir, x.path.name.lower()))
                for child_item in sorted_children:
                    children.append(_build_node(child_item.path, child_item.is_dir))
            node["children"] = children
            
        return node

    return {
        "meta": {"root": dir_path.name, "path": str(dir_path.resolve())},
        "stats": {"directories": result.stats["dirs"], "files": result.stats["files"]},
        "tree": _build_node(dir_path, True)
    }

def build_json_with_contents(dir_path: Path, config: ScanConfig, result: TraversalResult) -> Dict[str, Any]:
    """源文件内容"""
    json_data = build_json_structure(dir_path, config, result)
    contents = {}
    
    for item in result.text_files:
        c = result.get_content(item, quiet=True)
        if c:
            contents[str(item.relative_path)] = c
            
    json_data["contents"] = contents
    return json_data

def write_json(data: Dict[str, Any], output_file: Path) -> bool:
    """格式化JSON文件"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        from seedling.core.logger import logger
        logger.error(f"Failed to write JSON: {e}")
        return False