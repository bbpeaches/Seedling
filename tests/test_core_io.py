import pytest #type: ignore
from pathlib import Path
from seedling.core.io import extract_file_contents, get_dynamic_fence, is_safe_path

def test_get_dynamic_fence():
    # 无嵌套反引号
    assert get_dynamic_fence("print(123)") == "```"
    # 嵌套了 3 个反引号，应该生成 4 个
    code_with_fence = "```python\nprint(1)\n```"
    assert get_dynamic_fence(code_with_fence) == "````"
    # 嵌套了 4 个反引号，应该生成 5 个
    assert get_dynamic_fence("````md\ntext\n````") == "`````"

def test_is_safe_path(tmp_path):
    target_dir = tmp_path / "sandbox"
    target_dir.mkdir()
    
    # 安全路径
    assert is_safe_path(target_dir / "src/main.py", target_dir) is True
    # 路径穿越攻击
    assert is_safe_path(target_dir / "../../etc/passwd", target_dir) is False
    # 与根目录平级的路径
    assert is_safe_path(tmp_path / "other_dir", target_dir) is False

def test_extract_file_contents_with_nested_fences(tmp_path):

    md_content = """
### FILE: doc.md
````md
# Title
```python
print("nested")
```
````
"""
    test_file = tmp_path / "report.md"
    test_file.write_text(md_content, encoding='utf-8')
    contents = extract_file_contents(test_file)
    
    assert "doc.md" in contents
    assert 'print("nested")' in contents["doc.md"]