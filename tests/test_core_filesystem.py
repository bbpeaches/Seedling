import pytest #type: ignore
from pathlib import Path
from seedling.core.filesystem import is_text_file, matches_exclude_pattern, is_valid_item, ScanConfig

def test_is_text_file():
    assert is_text_file(Path("main.py")) is True
    assert is_text_file(Path("Dockerfile")) is True
    assert is_text_file(Path("image.png")) is False

def test_matches_exclude_pattern(tmp_path):
    base_dir = tmp_path
    
    # 构造目录结构
    (base_dir / "build").mkdir()
    (base_dir / "src/build").mkdir(parents=True)
    (base_dir / "src/main.py").touch()
    
    # 路径锚定规则 (/build/) 应该只拦截根目录下的 build
    anchored_excludes = ["/build/"]
    assert matches_exclude_pattern(base_dir / "build", base_dir, anchored_excludes) is True
    assert matches_exclude_pattern(base_dir / "src/build", base_dir, anchored_excludes) is False
    
    # 全局规则 (node_modules) 应该拦截任何深度的匹配
    global_excludes = ["node_modules"]
    assert matches_exclude_pattern(base_dir / "node_modules", base_dir, global_excludes) is True
    assert matches_exclude_pattern(base_dir / "src/node_modules", base_dir, global_excludes) is True

def test_is_valid_item(tmp_path):
    base_dir = tmp_path
    hidden_file = base_dir / ".env"
    hidden_file.touch()
    
    # 测试隐藏文件拦截
    config_hide = ScanConfig(show_hidden=False)
    assert is_valid_item(hidden_file, base_dir, config_hide) is False
    
    # 测试隐藏文件放行
    config_show = ScanConfig(show_hidden=True)
    assert is_valid_item(hidden_file, base_dir, config_show) is True
    
    # 测试文本过滤
    config_text = ScanConfig(text_only=True)
    png_file = base_dir / "test.png"
    png_file.touch()  
    assert is_valid_item(png_file, base_dir, config_text) is False