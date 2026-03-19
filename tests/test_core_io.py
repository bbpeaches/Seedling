import pytest # type: ignore
from pathlib import Path
from seedling.core.io import extract_tree_block, extract_file_contents

def test_extract_file_contents_with_nested_fences(tmp_path):
    md_content = """
# Dummy Report
### FILE: src/main.py
```python
def hello():
    print("Hello")
```

### FILE: docs/readme.md
````md
# Nested Doc
Here is code:
```bash
echo "nested"
```
````
"""
    test_file = tmp_path / "report.md"
    test_file.write_text(md_content, encoding='utf-8')
    
    contents = extract_file_contents(test_file)
    
    assert "src/main.py" in contents
    assert "docs/readme.md" in contents
    
    # 确保内部的 ``` 没有截断外层的 ````
    assert '```bash\necho "nested"\n```' in contents["docs/readme.md"]