import sys
import pytest # type: ignore
from seedling.commands.scan.skeleton import extract_skeleton

# 如果是 Python 3.8 及以下，跳过这些测试
pytestmark = pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")

def test_extract_skeleton_basic_function():
    source_code = """
def calculate_sum(a, b):
    # Some internal comment
    result = a + b
    print("Computing...")
    return result
"""
    expected_output = """def calculate_sum(a, b):
    ..."""
    
    result = extract_skeleton(source_code)
    assert "..." in result
    assert "print" not in result
    assert "calculate_sum" in result

def test_extract_skeleton_class_with_docstring():
    source_code = """
class MyModel:
    \"\"\"This is the core model.\"\"\"
    def __init__(self):
        self.data = []
        
    async def fetch(self):
        await asyncio.sleep(1)
        return self.data
"""
    result = extract_skeleton(source_code)
    assert '"""This is the core model."""' in result
    assert 'def __init__(self):' in result
    assert 'async def fetch(self):' in result
    assert 'asyncio.sleep' not in result

def test_extract_skeleton_syntax_error_fallback():
    # 故意制造语法错误的代码
    bad_code = "def broken_func(a, b) return a+b"
    result = extract_skeleton(bad_code)
    # 发生语法错误时，引擎应当优雅降级，返回原代码而不崩溃
    assert result == bad_code