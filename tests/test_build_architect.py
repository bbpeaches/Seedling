import pytest #type: ignore
from seedling.core.io import is_safe_path

def test_is_safe_path_logic():
    from pathlib import Path
    base = Path("/Users/kaelen/app")
    
    # 正常的深度嵌套
    assert is_safe_path(base / "a/b/c/d.txt", base) is True
    # 诡异但合法的相对路径点
    assert is_safe_path(base / "./src/../src/main.py", base) is True