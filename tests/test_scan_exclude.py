import pytest # type: ignore
from pathlib import Path
from unittest.mock import patch
from seedling.commands.scan.exclude import expand_excludes

def test_expand_excludes_with_gitignore(tmp_path):
    # 在临时目录创建一个假的 .gitignore
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("node_modules\n*.log\n# this is comment\n\n__pycache__/")
    
    # 切换当前工作目录到临时目录以便测试
    import os
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        raw_excludes = [".gitignore", "extra_rule"]
        result = expand_excludes(raw_excludes)
        
        assert "node_modules" in result
        assert "*.log" in result
        assert "__pycache__/" in result
        assert "extra_rule" in result
        assert "# this is comment" not in result
    finally:
        os.chdir(original_cwd)

@patch("seedling.commands.scan.exclude.ask_yes_no")
def test_expand_excludes_interactive_prompt(mock_ask, tmp_path):
    # 模拟一个普通文本文件，触发询问
    custom_rule = tmp_path / "my_rules.txt"
    custom_rule.write_text("secret_dir")
    
    import os
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # 模拟用户输入 "n" (不作为规则文件读取，当作纯 glob 字符串)
        mock_ask.return_value = False
        result_no = expand_excludes(["my_rules.txt"])
        assert result_no == ["my_rules.txt"]
        
        # 模拟用户输入 "y" (读取文件内容)
        mock_ask.return_value = True
        result_yes = expand_excludes(["my_rules.txt"])
        assert "secret_dir" in result_yes
    finally:
        os.chdir(original_cwd)