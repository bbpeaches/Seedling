#!/bin/bash

# ==============================================================================
# 🌲 Seedling Automated Test Suite
# Run this script to automatically test all core features of Seedling.
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   🚀 Starting Seedling E2E Test Suite... ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Test Environment Setup
TEST_DIR="seedling_test_sandbox"
OUT_DIR="${TEST_DIR}_out"

echo -e "\n${GREEN}[1/7] Setting up dummy project environment...${NC}"
rm -rf $TEST_DIR $OUT_DIR
mkdir -p $TEST_DIR/src $TEST_DIR/node_modules $TEST_DIR/.hidden $OUT_DIR

echo "print('Hello World')" > $TEST_DIR/src/main.py
echo "def add(a, b): return a + b" > $TEST_DIR/src/utils.py
echo "Heavy JS garbage" > $TEST_DIR/node_modules/junk.js
echo "Secret API Key: 12345" > $TEST_DIR/.hidden/secret.key
echo "# My Awesome App" > $TEST_DIR/README.md

# Basic Scan & Formats
echo -e "\n${GREEN}[2/7] Testing Basic Scans & Output Formats...${NC}"
scan $TEST_DIR -F txt -o $OUT_DIR -n basic_scan.txt
scan $TEST_DIR -F md -o $OUT_DIR -n basic_scan.md

if [ ! -f "$OUT_DIR/basic_scan.txt" ] || [ ! -f "$OUT_DIR/basic_scan.md" ]; then
    echo -e "${RED}❌ Basic scan failed to create files.${NC}"; exit 1
fi

# Exclusions & Hidden
echo -e "\n${GREEN}[3/7] Testing Exclusion & Hidden flags...${NC}"
scan $TEST_DIR -s -e node_modules -o $OUT_DIR -n clean_scan.md
if grep -q "junk.js" "$OUT_DIR/clean_scan.md"; then
    echo -e "${RED}❌ Exclude flag failed! Found node_modules content.${NC}"; exit 1
fi
if ! grep -q "secret.key" "$OUT_DIR/clean_scan.md"; then
    echo -e "${RED}❌ Show hidden flag failed! Could not find .hidden content.${NC}"; exit 1
fi

# Power Mode / Full Context
echo -e "\n${GREEN}[4/7] Testing POWER MODE (--full) context aggregation...${NC}"
scan $TEST_DIR --full -e node_modules -o $OUT_DIR -n snapshot.md
if ! grep -q "def add(a, b)" "$OUT_DIR/snapshot.md"; then
    echo -e "${RED}❌ Power mode failed to extract source code!${NC}"; exit 1
fi

# Find Mode
echo -e "\n${GREEN}[5/7] Testing Find Mode (Exact & Fuzzy)...${NC}"
scan $TEST_DIR -f "main" -o $OUT_DIR -n search_exact.md
scan $TEST_DIR -f "util" -o $OUT_DIR -n search_fuzzy.md
if ! grep -q "MATCHED" "$OUT_DIR/search_exact.md"; then
    echo -e "${RED}❌ Search mode failed to generate highlighted tree.${NC}"; exit 1
fi

# Direct Build
echo -e "\n${GREEN}[6/7] Testing Build - Direct Mode (-d)...${NC}"
build -d $OUT_DIR/direct_folder
build -d $OUT_DIR/direct_file.txt
if [ ! -d "$OUT_DIR/direct_folder" ] || [ ! -f "$OUT_DIR/direct_file.txt" ]; then
    echo -e "${RED}❌ Build direct mode failed to create files/folders.${NC}"; exit 1
fi

# Context Rehydration & Force
echo -e "\n${GREEN}[7/7] Testing EPISODIC MAGIC: Context Rehydration...${NC}"
build $OUT_DIR/snapshot.md $OUT_DIR/restored_project --force

if [ ! -f "$OUT_DIR/restored_project/src/main.py" ]; then
    echo -e "${RED}❌ Rehydration failed to build directory structure.${NC}"; exit 1
fi
if ! grep -q "Hello World" "$OUT_DIR/restored_project/src/main.py"; then
    echo -e "${RED}❌ Rehydration failed to inject source code back into files!${NC}"; exit 1
fi

echo -e "\n${BLUE}======================================================${NC}"
echo -e "${GREEN}  🎉 ALL TESTS PASSED SUCCESSFULLY! Seedling is ROCK SOLID! ${NC}"
echo -e "${BLUE}======================================================${NC}"
rm -rf $TEST_DIR $OUT_DIR