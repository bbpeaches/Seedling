import pytest #type: ignore
from pathlib import Path
from seedling.core.config import ScanConfig
from seedling.core.detection import is_text_file
from seedling.core.patterns import matches_exclude_pattern, is_valid_item

def test_is_text_file():
    assert is_text_file(Path("main.py")) is True
    assert is_text_file(Path("Dockerfile")) is True
    assert is_text_file(Path("image.png")) is False

def test_matches_exclude_pattern(tmp_path):
    base_dir = tmp_path
    
    (base_dir / "build").mkdir()
    (base_dir / "src/build").mkdir(parents=True)
    (base_dir / "src/main.py").touch()
    
    anchored_excludes = ["/build/"]
    assert matches_exclude_pattern(base_dir / "build", base_dir, anchored_excludes) is True
    assert matches_exclude_pattern(base_dir / "src/build", base_dir, anchored_excludes) is False
    
    global_excludes = ["node_modules"]
    assert matches_exclude_pattern(base_dir / "node_modules", base_dir, global_excludes) is True
    assert matches_exclude_pattern(base_dir / "src/node_modules", base_dir, global_excludes) is True

def test_is_valid_item(tmp_path):
    base_dir = tmp_path
    hidden_file = base_dir / ".env"
    hidden_file.touch()
    
    config_hide = ScanConfig(show_hidden=False)
    assert is_valid_item(hidden_file, base_dir, config_hide) is False
    
    config_show = ScanConfig(show_hidden=True)
    assert is_valid_item(hidden_file, base_dir, config_show) is True
    
    config_text = ScanConfig(text_only=True)
    png_file = base_dir / "test.png"
    png_file.touch()  
    assert is_valid_item(png_file, base_dir, config_text) is False