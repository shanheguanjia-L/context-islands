#!/usr/bin/env python3
"""把 check.py --json 的結果寫成「演化看板」issue 的內文（GitHub Actions 每週用）。

用法：python3 tools/board.py check.json > board.md
沒有待辦時只印一行 NOTHING_TO_DO。
"""
import json
import sys


def render(res):
    errs, due, skipped = res.get("errors") or [], res.get("due") or [], res.get("skipped") or []
    if not errs and not due and not skipped:
        return "NOTHING_TO_DO"
    out = [f"內容版本 {res.get('content_version')}，{res.get('islands')} 座島。這張看板每週一自動更新，沒有待辦時會自動關閉。", ""]
    if errs:
        out += [f"## 體檢錯誤 {len(errs)} 項（要先修）", ""] + [f"- {e}" for e in errs] + [""]
    if due:
        out += [f"## 該重新驗證 {len(due)} 座", "",
                "這些島裡有依賴當下工具的說法，超過期限沒人確認過。實際跑一次實驗，說法還成立就更新 `meta.js` 的 checked；不成立就改內容。", ""]
        for d in due:
            w = f"：{'；'.join(d['watch'])}" if d.get("watch") else ""
            out.append(f"- [ ] **{d['name']}**（上次 {d['checked']}，{d['age_days']} 天前）{w}")
        out.append("")
    if skipped:
        out += ["## 這次沒查到（不算通過）", ""] + [f"- {s}" for s in skipped] + [""]
    out += ["---", "維護者在本機執行 `python3 tools/evolve.py --draft 2`，會把這裡的事和學員回報交給 AI 起草，驗收過的才留下分支。"]
    return "\n".join(out)


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        print(render(json.load(f)))
