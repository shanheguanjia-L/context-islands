#!/usr/bin/env python3
"""從繁體中文原稿產生簡體中文版（zh-hans/）。

繁體版是正本：改內容請改根目錄的 index.html、data.js、課程設計.md，
再執行本腳本重新產生簡體版，不要直接改 zh-hans/ 裡的檔案。

用法：
    pip install opencc-python-reimplemented   # 或 opencc
    python3 tools/build_zh_hans.py

轉換用 OpenCC 的 tw2sp（台灣正體 → 大陸簡體，含常用詞彙轉換），
再套用下方 FIXES 補上 OpenCC 沒處理、或課程裡需要在地化的詞。
"""
import pathlib
import sys

try:
    import opencc
except ImportError:
    sys.exit("找不到 opencc，請先 pip install opencc-python-reimplemented")

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "zh-hans"
CC = opencc.OpenCC("tw2sp")

# 轉換後再替換（左邊是 OpenCC 轉完的簡體字串）
FIXES = [
    ("脉络群岛", ""),          # 品牌名先保護起來
    ("脉络工程", "上下文工程"),
    ("脉络窗口", "上下文窗口"),
    ("脉络", "上下文"),
    ("", "脉络群岛"),
    ("范例", "示例"),
    ("预设", "默认"),
    ("品质", "质量"),
    ("回馈", "反馈"),
    ("原子笔", "圆珠笔"),
    ("新进同仁", "新同事"),
    ("新台币", "人民币"),
    ("台湾的首都是哪里", "中国的首都是哪里"),
    ("工作天", "工作日"),
    ("讯息", "消息"),
    ("zh-Hant-TW", "zh-Hans"),
    ('href="icons/', 'href="../icons/'),  # 網站圖示在根目錄
    ('<script src="meta.js">', '<script src="../meta.js">'),  # 演化紀錄四語共用一份
    ("更新纪录.md", "更新紀錄.md"),  # 連到倉庫裡的檔名，不能轉成簡體
    ("演化机制.md", "演化機制.md"),
    ("照片回传", "照片发回来"),
    ("矢量", "向量"),
    ("日圆", "日元"),
    ("第四季预算", "第四季度预算"),
    ("住饭店", "住酒店"),
    ("回传让它修正", "返回给它修正"),
    # 大陆习惯用弯引号
    ("「", "“"), ("」", "”"), ("『", "‘"), ("』", "’"),
]

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import langs  # noqa: E402


def convert(text: str) -> str:
    out = CC.convert(text)
    for a, b in FIXES:
        out = out.replace(a, b)
    return out


def main() -> None:
    OUT.mkdir(exist_ok=True)

    html = convert((ROOT / "index.html").read_text(encoding="utf-8"))
    html = langs.apply(html, "zh-hans/")
    (OUT / "index.html").write_text(html, encoding="utf-8")

    (OUT / "data.js").write_text(convert((ROOT / "data.js").read_text(encoding="utf-8")), encoding="utf-8")
    (OUT / "课程设计.md").write_text(convert((ROOT / "課程設計.md").read_text(encoding="utf-8")), encoding="utf-8")

    print("已產生：", ", ".join(p.name for p in sorted(OUT.iterdir())))


if __name__ == "__main__":
    main()
