import pytest #type: ignore
import os
from pathlib import Path
from unittest.mock import patch
from seedling.core.filesystem import scan_dir_lines, ScanConfig

def test_empty_dir_scan(tmp_path):
    """扫描一个空目录"""
    stats = {"dirs": 0, "files": 0}
    config = ScanConfig()
    lines = scan_dir_lines(tmp_path, config, stats)
    
    # 预期：不应该有树状行，统计为 0
    assert len(lines) == 0
    assert stats["dirs"] == 0
    assert stats["files"] == 0

def test_filesystem_permission_error(tmp_path):
    """权限不足的目录"""
    stats = {"dirs": 0, "files": 0}
    config = ScanConfig()
    
    # 创建一个子目录，并模拟在进入它时抛出 PermissionError
    locked_dir = tmp_path / "secret_vault"
    locked_dir.mkdir()
    
    # 我们拦截 Path.iterdir，当访问特定目录时抛出异常
    with patch.object(Path, 'iterdir') as mock_iter:
        mock_iter.side_effect = PermissionError("Access Denied")
        
        lines = scan_dir_lines(tmp_path, config, stats)
        assert any("[Permission Denied" in line for line in lines)

def test_broken_symlink_handling(tmp_path):
    """断链符号链接 """
    stats = {"dirs": 0, "files": 0}
    config = ScanConfig()
    
    # 创建一个指向不存在文件的软连接
    target = tmp_path / "non_existent.txt"
    link = tmp_path / "my_link"
    os.symlink(str(target), str(link))
    
    lines = scan_dir_lines(tmp_path, config, stats)
    assert any("my_link (symlink)" in line for line in lines)
    assert stats["files"] == 1

def test_circular_symlink_recursion_protection(tmp_path):
    """循环软连接保护 (A -> B -> A)"""
    stats = {"dirs": 0, "files": 0}
    config = ScanConfig()
    
    # 创建循环引用：dir_a/link_to_a -> dir_a
    dir_a = tmp_path / "dir_a"
    dir_a.mkdir()
    os.symlink(str(dir_a), str(dir_a / "link_to_a"))
    
    lines = scan_dir_lines(tmp_path, config, stats)
    
    assert any("link_to_a/ (symlink)" in line for line in lines)
    assert stats["dirs"] == 2

def test_long_path_scan(tmp_path):
    """测试深层级/超长路径）"""
    stats = {"dirs": 0, "files": 0}
    config = ScanConfig(max_depth=5)
    
    curr = tmp_path
    for i in range(10):
        curr = curr / f"very_long_folder_name_{i}"
        curr.mkdir()
    
    lines = scan_dir_lines(tmp_path, config, stats)
    # 验证当 depth > max_depth 时，逻辑是否正确截断
    assert stats["dirs"] == 5