import pytest # type: ignore
from pathlib import Path
from seedling.core.filesystem import is_text_file, matches_exclude_pattern, is_valid_item

def test_is_text_file():
    # 测试常规后缀
    assert is_text_file(Path("main.py")) == True
    assert is_text_file(Path("index.html")) == True
    # 测试特殊名称
    assert is_text_file(Path("Dockerfile")) == True
    assert is_text_file(Path(".gitignore")) == True
    # 测试非文本
    assert is_text_file(Path("image.png")) == False
    assert is_text_file(Path("app.exe")) == False

def test_matches_exclude_pattern(tmp_path):
    base_dir = tmp_path
    
    # 模拟文件和目录结构
    pycache_dir = base_dir / "seedling" / "__pycache__"
    pycache_dir.mkdir(parents=True)
    
    test_file = pycache_dir / "test.pyc"
    test_file.touch()
    
    normal_file = base_dir / "src" / "main.py"
    normal_file.parent.mkdir()
    normal_file.touch()

    excludes = ["__pycache__/", "*.pyc", "build"]

    # 规则 1: 目录带斜杠拦截 (应拦截 __pycache__ 目录)
    assert matches_exclude_pattern(pycache_dir, base_dir, excludes) == True
    
    # 规则 2: 文件名通配符拦截 (应拦截 test.pyc)
    assert matches_exclude_pattern(test_file, base_dir, excludes) == True
    
    # 规则 3: 正常文件不应被拦截
    assert matches_exclude_pattern(normal_file, base_dir, excludes) == False

def test_is_valid_item(tmp_path):
    base_dir = tmp_path
    hidden_file = base_dir / ".env"
    hidden_file.touch()
    
    # 测试隐藏文件拦截
    assert is_valid_item(hidden_file, base_dir, show_hidden=False, excludes=[], text_only=False) == False
    assert is_valid_item(hidden_file, base_dir, show_hidden=True, excludes=[], text_only=False) == True