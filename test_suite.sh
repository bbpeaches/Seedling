#!/bin/bash

# ==============================================================================
# 🌲 Seedling Ultimate Automated Test Suite (v2.3.2 Refined)
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   🚀 Starting Seedling ULTIMATE E2E Test Suite... ${NC}"
echo -e "${BLUE}======================================================${NC}"

TEST_DIR="$HOME/tmp/seedling_test_sandbox"
OUT_DIR="$HOME/tmp/seedling_test_out"

# ==============================================================================
# TEST SUITE 1: Legacy Core Engine & Hardening Tests
# ==============================================================================

echo -e "\n${GREEN}[1/2] Executing Core Engine & Hardening Tests...${NC}"

echo -e "  -> [Setup] Creating COMPLEX dummy project in $HOME/tmp..."
if [[ "$TEST_DIR" != "$HOME/tmp/"* || "$OUT_DIR" != "$HOME/tmp/"* ]]; then
    echo -e "${RED}❌ CRITICAL: Invalid test directory path detected!${NC}"
    exit 1
fi

rm -rf "$TEST_DIR" "$OUT_DIR"
mkdir -p "$TEST_DIR/src/nested/deep" "$TEST_DIR/node_modules" "$TEST_DIR/.hidden" "$OUT_DIR"
mkdir -p "$TEST_DIR/build/logs" "$TEST_DIR/src/build" # 用于测试路径锚定规则

# Standard Data
echo "print('Hello World')" > "$TEST_DIR/src/main.py"
echo "def add(a, b): return a + b" > "$TEST_DIR/src/nested/utils.py"
echo "# My Awesome App" > "$TEST_DIR/README.md"
echo "fake_binary" > "$TEST_DIR/image.png"

# Malicious Blueprints for Path Traversal Test
cat << 'EOF' > "$TEST_DIR/malicious.md"
# 恶意蓝图
```text
root/
└── ../../../escaped.txt
```
EOF

echo -e "  -> Testing Basic Scans & Directory Trailing Slashes (/)..."
scan "$TEST_DIR" -F txt -o "$OUT_DIR" -n basic_scan.txt >/dev/null
if ! grep -q "src/" "$OUT_DIR/basic_scan.txt"; then
    echo -e "${RED}❌ Trailing slash feature failed!${NC}"; exit 1
fi

echo -e "  -> Testing Find Mode (Exact & Highlighting)..."
scan "$TEST_DIR" -f "main" --full -o "$OUT_DIR" -n search_exact.md >/dev/null
if ! grep -q "MATCHED" "$OUT_DIR/search_exact.md"; then
    echo -e "${RED}❌ Search mode failed to generate highlighted 🎯 tree.${NC}"; exit 1
fi

echo -e "  -> Testing SECURITY: Dangerous Deletion TTY Interception..."
OUTPUT=$(echo "CONFIRM DELETE" | scan "$TEST_DIR" -f "none" --delete 2>&1 || true)
if [[ ! "$OUTPUT" == *"interactive terminal"* ]]; then
    echo -e "${RED}❌ Security Bypass! TTY check failed.${NC}"; exit 1
fi

echo -e "  -> Testing SECURITY: Path Traversal Interception..."
build "$TEST_DIR/malicious.md" "$OUT_DIR/safe_build" --force >/dev/null 2>&1 || true
if [ -f "$OUT_DIR/escaped.txt" ] || [ -f "escaped.txt" ]; then
    echo -e "${RED}❌ CRITICAL: Security Bypass! Path traversal succeeded.${NC}"; exit 1
fi

echo -e "  -> Testing SECURITY: Image Memory Bomb Limit..."
mkdir -p "$TEST_DIR/huge_dir"
seq 1 1505 | xargs -I {} touch "$TEST_DIR/huge_dir/file_{}.txt"
OUTPUT=$(scan "$TEST_DIR/huge_dir" -F image -o "$OUT_DIR" -n "huge.png" 2>&1 || true)
if [[ ! "$OUTPUT" == *"aborted to prevent memory overflow"* ]]; then
    echo -e "${RED}❌ Image memory bomb check failed!${NC}"; exit 1
fi

# ==============================================================================
# TEST SUITE 2: v2.3.2 Refactoring & New Feature Tests
# ==============================================================================

echo -e "\n${GREEN}[2/2] Executing v2.3.2 Refactoring & New Feature Tests...${NC}"

echo -e "  -> Testing UX: Flag Conflict Intercept (--full vs --skeleton)..."
# 验证互斥参数组是否生效。重构后，同时传入这两个参数应当报错并退出。
if scan "$TEST_DIR" --full --skeleton 2>&1 | grep -Eiq "conflicting|not allowed|cannot be used together"; then
    echo -e "     ✅ Correcty blocked conflicting flags."
else
    echo -e "${RED}❌ UX Failure: Should have blocked simultaneous --full and --skeleton flags.${NC}"; exit 1
fi

echo -e "  -> Testing ENGINE: Smart Exclude with Root Path Anchoring (/build/)..."
cat << 'EOF' > "$TEST_DIR/.myignore"
/build/
*.log
EOF
# 在 v2.3.1+ 中，/build/ 应该只忽略根目录下的 build，不影响 src/build
scan "$TEST_DIR" -e "$TEST_DIR/.myignore" -o "$OUT_DIR" -n "anchoring_test.md" >/dev/null
if grep -q "build/logs" "$OUT_DIR/anchoring_test.md"; then
    echo -e "${RED}❌ Anchoring failed! /build/ should have ignored the root build directory.${NC}"; exit 1
fi
if ! grep -A 2 "src/" "$OUT_DIR/anchoring_test.md" | grep -q "build/"; then
    echo -e "${RED}❌ Over-filtering! /build/ should NOT have ignored src/build/.${NC}"; exit 1
fi

echo -e "  -> Testing ENGINE: AST Code Skeleton Extraction (--skeleton)..."
if python3 -c "import ast; hasattr(ast, 'unparse') or exit(1)" 2>/dev/null; then
    cat << 'EOF' > "$TEST_DIR/src/ast_complex.py"
class DataModel:
    """This is the core data model."""
    def compute(self):
        print("Complex logic here")
        return 42
EOF
    scan "$TEST_DIR" --skeleton -o "$OUT_DIR" -n "skeleton.md" >/dev/null
    if ! grep -q "class DataModel:" "$OUT_DIR/skeleton.md"; then
        echo -e "${RED}❌ Skeleton extraction failed to preserve class structure.${NC}"; exit 1
    fi
    if grep -q "Complex logic" "$OUT_DIR/skeleton.md"; then
        echo -e "${RED}❌ Skeleton extraction failed to strip implementation logic.${NC}"; exit 1
    fi
else
    echo -e "${YELLOW}     ⚠️  Skipping AST test: Python < 3.9.${NC}"
fi

echo -e "  -> Testing UX: Streamlined Search CLI Intercept (No report file)..."
rm -f "$OUT_DIR/quick_search.md"
scan "$TEST_DIR" -f "main" -o "$OUT_DIR" -n "quick_search.md" >/dev/null
if [ -f "$OUT_DIR/quick_search.md" ]; then
    echo -e "${RED}❌ Streamlined Search failed! Generated a file without --full.${NC}"; exit 1
fi

echo -e "  -> Testing ENGINE: Search Power Mode (Report + Code)..."
scan "$TEST_DIR" -f "utils" --full -o "$OUT_DIR" -n "search_full_report.md" >/dev/null
if [ ! -f "$OUT_DIR/search_full_report.md" ] || ! grep -q "def add(a, b)" "$OUT_DIR/search_full_report.md"; then
    echo -e "${RED}❌ Search Power Mode failed to bundle source code.${NC}"; exit 1
fi

# ==============================================================================
# FINAL CLEANUP & SUCCESS
# ==============================================================================

echo -e "\n${BLUE}======================================================${NC}"
echo -e "${GREEN}   🏆 ALL TESTS PASSED! Seedling v2.3.2 is UNBREAKABLE! ${NC}"
echo -e "${BLUE}======================================================${NC}"

if [[ "$TEST_DIR" == "$HOME/tmp/"* && "$OUT_DIR" == "$HOME/tmp/"* ]]; then
    rm -rf "$TEST_DIR" "$OUT_DIR"
fi