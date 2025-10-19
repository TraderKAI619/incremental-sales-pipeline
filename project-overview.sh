#!/bin/bash
echo "=== PROJECT STRUCTURE ==="
tree -L 3 -I '.venv|__pycache__|.git|node_modules' || find . -maxdepth 3 -type d | grep -v ".git\|__pycache__\|.venv"

echo -e "\n=== KEY FILES ==="
ls -la | grep -E '\.(yml|yaml|json|txt|md)$|Makefile'

echo -e "\n=== PYTHON SCRIPTS ==="
find . -name "*.py" -not -path "./.venv/*" -not -path "./__pycache__/*" | head -20

echo -e "\n=== DEPENDENCIES ==="
cat requirements.txt 2>/dev/null || echo "No requirements.txt found"

echo -e "\n=== RECENT COMMITS ==="
git log --oneline -5 2>/dev/null || echo "Not a git repository"

echo -e "\n=== GIT STATUS ==="
git status -s 2>/dev/null || echo "Not a git repository"
