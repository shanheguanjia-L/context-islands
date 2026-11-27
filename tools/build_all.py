#!/usr/bin/env python3
"""一行重建全部產生檔（語言切換、簡體版、英文版、日文版），再跑一次體檢。

用法：python3 tools/build_all.py
簡體版要用裝了 OpenCC 1.4.2 的 Python；找不到就跳過並明講。指定方式：環境變數 OPENCC_PYTHON，
或寫在 .evolve/local.json：{"opencc_python": "/path/to/python3"}（不進版控）。
"""
import pathlib
import subprocess
import sys

TOOLS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import check  # noqa: E402

errs, skipped = check.run_builders()
for e in errs:
    print("✗ " + e)
for s in skipped:
    print("? 這次沒重建：" + s)
if errs:
    sys.exit(1)
print("產生檔已重建，接著體檢：\n")
sys.exit(subprocess.run([sys.executable, str(TOOLS / "check.py"), "--no-generated"]).returncode)
