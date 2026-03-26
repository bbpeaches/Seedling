import pytest #type: ignore
import os
from pathlib import Path
from unittest.mock import patch
from seedling.core.config import ScanConfig
from seedling.core.traversal import traverse_directory, build_tree_lines

def test_empty_dir_scan(tmp_path):
    """扫描一个空目录"""
    config = ScanConfig()
    result = traverse_directory(tmp_path, config)
    lines = build_tree_lines(result, config, root_path=tmp_path)
    
    assert len(lines) == 0
    assert result.stats["dirs"] == 0
    assert result.stats["files"] == 0

def test_filesystem_permission_error(tmp_path):
    """权限不足的目录"""
    config = ScanConfig()
    locked_dir = tmp_path / "secret_vault"
    locked_dir.mkdir()
    
    with patch.object(Path, 'iterdir') as mock_iter:
        mock_iter.side_effect = PermissionError("Access Denied")
        # 权限错误应该被静默忽略（或只在 json 输出中体现），不会抛出崩溃
        result = traverse_directory(tmp_path, config)
        assert result.stats["dirs"] == 0 # 没有成功读取到内部

def test_broken_symlink_handling(tmp_path):
    """断链符号链接"""
    config = ScanConfig()
    target = tmp_path / "non_existent.txt"
    link = tmp_path / "my_link"
    os.symlink(str(target), str(link))
    
    result = traverse_directory(tmp_path, config)
    lines = build_tree_lines(result, config, root_path=tmp_path)
    
    assert any("my_link (symlink)" in line for line in lines)
    assert result.stats["files"] == 1

def test_circular_symlink_recursion_protection(tmp_path):
    """循环软连接保护 (A -> B -> A)"""
    config = ScanConfig()
    dir_a = tmp_path / "dir_a"
    dir_a.mkdir()
    os.symlink(str(dir_a), str(dir_a / "link_to_a"))
    
    result = traverse_directory(tmp_path, config)
    lines = build_tree_lines(result, config, root_path=tmp_path)
    
    assert any("link_to_a/ (symlink)" in line for line in lines)
    assert result.stats["dirs"] == 2

def test_long_path_scan(tmp_path):
    """测试深层级/超长路径"""
    config = ScanConfig(max_depth=5)
    curr = tmp_path
    for i in range(10):
        curr = curr / f"very_long_folder_name_{i}"
        curr.mkdir()
    
    result = traverse_directory(tmp_path, config)
    # 验证深度截断是否生效（根目录0 + 深度5 = 5个子目录被计入）
    assert result.stats["dirs"] == 5