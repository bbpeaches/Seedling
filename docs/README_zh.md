# Seedling-tools

[![Seedling CI](https://img.shields.io/github/actions/workflow/status/bbpeaches/Seedling/ci.yml?branch=main&style=flat-square)](https://github.com/bbpeaches/Seedling/actions)
[![PyPI version](https://img.shields.io/pypi/v/seedling-tools.svg?style=flat-square&color=blue)](https://pypi.org/project/Seedling-tools/)
[![Python Versions](https://img.shields.io/pypi/pyversions/seedling-tools.svg?style=flat-square)](https://pypi.org/project/Seedling-tools/)
[![License](https://img.shields.io/github/license/bbpeaches/Seedling?style=flat-square)](https://github.com/bbpeaches/Seedling/blob/main/LICENSE)

**Seedling-tools** 是一款高性能的命令行工具包，专为代码库探索、智能分析以及大模型上下文聚合而设计。

核心功能：
1. **SCAN**：将目录树结构导出为 Markdown、TXT、JSON 或图片格式。
2. **FIND & GREP**：执行精确/模糊的文件名搜索，以及基于正则表达式的文件内容匹配。
3. **ANALYZE**：自动探测项目架构、核心依赖包及程序入口点。
4. **SKELETON**：基于 AST 提取 Python 代码结构，并自动剥离具体的实现逻辑。
5. **POWER MODE**：全量聚合整个代码仓库的源码，为 LLM 提示词投喂提供完整的上下文。
6. **BUILD**：根据纯文本蓝图逆向还原出真实的物理文件系统。

由统一单次遍历缓存引擎强力驱动。

其他语言版本阅读: [English](../README.md)

---

## 安装指南

Seedling-tools 推荐通过 `pipx` 进行全局安装，以确保干净的隔离环境。
```bash
pipx install Seedling-tools
```

### 一键安装脚本

  * **Windows**: 运行 `./install.bat`
  * **macOS / Linux**: 运行 `bash install.sh`

### 开发者 / 手动安装

如果您需要修改源代码，请使用**可编辑模式 (Editable Mode)**：

```bash
pipx install -e . --force
```

-----

## 作为 Python 库使用

您现在可以通过 `ScanConfig` 引擎直接在 Python 代码中使用 Seedling 的核心功能：

```python
import seedling
from seedling.core.config import ScanConfig
from seedling.core.traversal import traverse_directory, build_tree_lines

# 初始化配置
config = ScanConfig(max_depth=2, quiet=True)

# 获取内存快照
result = traverse_directory("./src", config)

# 渲染树状线条
lines = build_tree_lines(result, config)
print("\n".join(lines))
```

-----

## CLI 命令参考

Seedling-tools 采用清晰、显式的参数系统。

### 1. `scan` - 探索器

用于扫描目录、提取代码骨架或搜索项目。注意：`--full` 和 `--skeleton` 为互斥参数。

| 参数 | 描述 |
| --- | --- |
| `target` | 要扫描或搜索的目标目录 (默认为 `.`)。 |
| `--find`, `-f` | **搜索模式**。快速 CLI 搜索 (精确匹配 & 模糊匹配)。结合 `--full` 可导出代码报告。 |
| `--format`, `-F` | 输出格式：`md` (默认), `txt`, `json`, 或 `image`。 |
| `--name`, `-n` | 自定义输出文件名。 |
| `--outdir`, `-o` | 结果保存路径。 |
| `--showhidden` | 扫描时包含隐藏文件。 |
| `--depth`, `-d` | 最大递归深度。 |
| `--exclude`, `-e` | 排除项目列表。**智能解析：自动读取 `.gitignore` 文件或接受 Glob 模式**。 |
| `--include` | 仅包含匹配模式的文件/目录 (如 `--include "*.py"`)。 |
| `--type`, `-t` | 按文件类型过滤：`py`, `js`, `ts`, `cpp`, `go`, `java`, `rs`, `web`, `json`, `yaml`, `md`, `shell`, `all`。 |
| `--regex` | 将 `-f` 搜索模式视为正则表达式。 |
| `--grep`, `-g` | 在文件内容中搜索 (内容搜索模式)。 |
| `-C`, `--context` | 在 grep 匹配周围显示 N 行上下文。 |
| `--analyze` | 分析项目结构、类型、依赖和架构。 |
| `--full` | **强力模式 (Power Mode)**。附加所有扫描到的源文件的全文内容。 |
| `--skeleton` | **[实验性]** AST 代码骨架提取。剔除内部逻辑，保留签名。 |
| `--text` | **智能过滤**。仅扫描文本格式文件 (自动忽略二进制/多媒体文件)。 |
| `--delete` | **清理模式**。永久删除被 `--find` 匹配到的项目 (仅限交互式 TTY 终端可用)。 |
| `--dry-run` | 预览删除操作但不实际执行 (配合 `--delete` 使用)。 |
| `--verbose` / `-q`| 调试日志模式 (`-v`) 或静默模式 (`-q`)。 |

### 2. `build` - 建造师

将基于文本的树状图蓝图转换为真实的文件系统，或从快照中恢复项目。

| 参数 | 描述 |
| --- | --- |
| `file` | 源树状图蓝图文件 (`.txt` 或 `.md`)。 |
| `target` | 构建结构的存放位置 (默认为当前目录)。 |
| `--direct`, `-d` | **直达模式**。跳过提示，立即创建指定路径。 |
| `--check` | **预检模式 (Dry-Run)**。模拟构建过程，报告缺失/已存在的项目。 |
| `--force` | **强制覆盖**。直接覆盖已存在的文件而不跳过。 |

-----

## v2.4 新功能 - 修复与改进

### 安全性
- **`--dry-run` 模式**：在执行 `--delete` 前预览将要删除的内容：
  ```bash
  scan . -f "temp_*" --delete --dry-run
  ```

### 兼容性
- **`--skeleton` 需要 Python 3.9+**：为 Python 3.8 用户提供清晰的错误提示
- **Pillow 改为可选依赖**：仅在需要图片导出时安装 `pip install Seedling-tools[image]`

### 性能
- **精确内存计算**：修复内存追踪，防止高 Unicode 密度文件导致 OOM 崩溃
- **保守内存阈值**：降低至 80% 以增加安全余量

### JSON 输出模式
导出结构化 JSON 格式的目录结构，便于程序化处理：
```bash
scan . -F json -o structure.json
```

### 文件类型与 Include 过滤器
按文件类型或自定义模式过滤：
```bash
scan . --type py -d 3
scan . --include "*.md" --include "*.txt"
```

### 正则搜索模式
在搜索中使用正则表达式：
```bash
scan . -f "test_.*\.py" --regex
```

### 内容搜索 (Grep 模式)
在文件内容中搜索并显示上下文：
```bash
scan . --grep "TODO" -C 3 --type py
scan . -g "def main" -C 2
```

### 项目分析
分析项目结构和依赖：
```bash
scan . --analyze
```

-----

## 项目结构 (v2.4)

```text
Seedling/
├── docs/                      # 文档与更新日志
│   ├── CHANGELOG.md           # 英文更新日志
│   ├── CHANGELOG_zh.md        # 中文更新日志
│   └── README_zh.md           # 中文说明文档
├── seedling/                  # 核心包
│   ├── commands/              # CLI 命令路由
│   │   ├── build/             # 构建逻辑 (逆向工程)
│   │   │   ├── __init__.py    # 构建 CLI 路由与参数校验
│   │   │   └── architect.py   # 蓝图解析与安全物理构建
│   │   └── scan/              # 扫描逻辑 (探索与提取)
│   │       ├── __init__.py    # 中心路由与单次遍历触发器
│   │       ├── analyzer.py    # 项目架构与依赖智能分析
│   │       ├── exclude.py     # .gitignore 风格排除规则解析
│   │       ├── explorer.py    # 目录树渲染与通用格式导出
│   │       ├── full.py        # 强力模式 (大模型上下文全量聚合)
│   │       ├── grep.py        # 纯内存内容搜索与上下文提取
│   │       ├── json_output.py # 嵌套 JSON 结构化导出
│   │       ├── search.py      # 文件搜索 (精确/模糊) 与安全删除
│   │       └── skeleton.py    # Python AST 骨架提取 (逻辑剥离)
│   ├── core/                  # 共享核心引擎
│   │   ├── config.py          # 配置数据类与全局常量
│   │   ├── detection.py       # 文件类型与二进制内容探针
│   │   ├── io.py              # 文件读写、代码块边界碰撞与覆盖保护
│   │   ├── logger.py          # 集中式 CLI 终端格式化与日志级别设定
│   │   ├── patterns.py        # Glob/正则路径匹配引擎
│   │   ├── sysinfo.py         # 硬件内存探针与系统深度限制获取
│   │   ├── traversal.py       # 统一单次遍历缓存引擎
│   │   └── ui.py              # 交互式提示与动态进度条
│   ├── __init__.py            # 公开 API 暴露与包元数据
│   └── main.py                # CLI 入口路由
├── tests/                     # 单元测试 (核心机制、边缘场景、IO 安全等)
├── install.bat                # Windows 一键安装脚本
├── install.sh                 # Linux/macOS 一键安装脚本
├── LICENSE                    # MIT 开源许可证
├── pyproject.toml             # 构建配置与包元数据
├── pytest.ini                 # Pytest 测试配置文件
├── README.md                  # 项目主说明文档
└── test_suite.sh              # 自动化端到端 (E2E) 测试脚本
```

-----

## 变更日志

每一次发布的详细变更历史均记录于 [CHANGELOG.md](CHANGELOG.md) 文件中。
