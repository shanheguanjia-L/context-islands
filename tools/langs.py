"""各語言版本共用：右上角的語言切換區塊。

新增語言時，在 LANGS 加一行，再重跑所有 build_*.py。
根目錄 index.html 的 <!--LANG-->…<!--/LANG--> 區塊也用 `python3 tools/langs.py` 重新產生。
"""
import pathlib
import re

# (lang 屬性, 顯示名稱, 相對於根目錄的資料夾)
LANGS = [
    ("zh-Hant", "繁體中文", ""),
    ("zh-Hans", "简体中文", "zh-hans/"),
    ("en", "English", "en/"),
    ("ja", "日本語", "ja/"),
]

LANG_RE = re.compile(r"<!--LANG-->.*?<!--/LANG-->", re.S)


def lang_block(current_dir: str) -> str:
    """current_dir：這一頁所在的資料夾（根目錄是 ""）。產生連到其他語言的連結。"""
    up = "../" if current_dir else ""
    links = []
    for code, label, d in LANGS:
        if d == current_dir:
            continue
        href = (up + d) or "./"
        links.append(
            f'<a class="lang" href="{href}" '
            "onclick=\"this.href=this.getAttribute('href')+location.hash\" "
            f'lang="{code}">{label}</a>'
        )
    return "<!--LANG-->" + "".join(links) + "<!--/LANG-->"


def apply(html: str, current_dir: str) -> str:
    if not LANG_RE.search(html):
        raise SystemExit("找不到 <!--LANG--> 語言切換區塊")
    return LANG_RE.sub(lambda m: lang_block(current_dir), html)


if __name__ == "__main__":
    root = pathlib.Path(__file__).resolve().parent.parent / "index.html"
    root.write_text(apply(root.read_text(encoding="utf-8"), ""), encoding="utf-8")
    print("已更新根目錄 index.html 的語言切換區塊")
