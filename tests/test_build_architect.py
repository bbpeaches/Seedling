import pytest # type: ignore
from pathlib import Path
from seedling.commands.build.architect import is_safe_path

def test_is_safe_path(tmp_path):
    target_dir = tmp_path / "project_root"
    target_dir.mkdir()
    
    # 正常的内部路径
    safe_child = target_dir / "src" / "main.py"
    assert is_safe_path(safe_child, target_dir) == True
    
    # 试图跳出根目录的恶意路径 (../../../etc/passwd)
    malicious_path = target_dir / "src" / ".." / ".." / ".." / "etc" / "passwd"
    assert is_safe_path(malicious_path, target_dir) == False