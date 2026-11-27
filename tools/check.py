#!/usr/bin/env python3
"""課程體檢：內容合約、四語對齊、翻譯有沒有跟上、產生檔是不是最新、哪些島該重新驗證。

用法：
    python3 tools/check.py                 # 全部檢查，人看的報告；有錯誤時結束碼 1
    python3 tools/check.py --json          # 同上，輸出 JSON（給 evolve.py 和 GitHub Actions 用）
    python3 tools/check.py --accept-i18n   # 英日版翻好之後執行：把目前的繁中內容記成「英日已同步」
    python3 tools/check.py --accept-i18n en   # 只記英文（日文還沒翻完時）

「錯誤」會讓結束碼變 1（CI 會標紅）；「該重新驗證」只是待辦，不算錯誤。
沒辦法檢查的項目（例如這台電腦沒有 opencc）會列在「這次沒查到」，不會當成通過。

只用標準函式庫；讀 data.js 要有 node。
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
LOCK = TOOLS / "i18n.lock.json"
LANG_DIRS = {"zh": "", "zh-hans": "zh-hans/", "en": "en/", "ja": "ja/"}
TRANSLATED = ["en", "ja"]  # 人工翻譯、要跟著繁中改的語言
# 這些欄位只在繁中版有（內部標記，畫面不顯示），對齊時略過
ZH_ONLY_KEYS = {"fixes"}
# 有 watch（依賴當下工具的說法）的島，多久沒驗證就該重看；其他島
STALE_DAYS_WATCH = 90
STALE_DAYS_OTHER = 365
GENERATED = ["zh-hans/index.html", "zh-hans/data.js", "zh-hans/课程设计.md", "en/index.html", "ja/index.html", "index.html"]
BUILDERS = ["langs.py", "build_zh_hans.py", "build_en.py", "build_ja.py"]


# ---------- 讀資料 ----------
def node_bin():
    return shutil.which("node")


def load(lang):
    """回傳該語言 data.js（加上共用的 meta.js）放在 window 上的全部東西。"""
    files = [str(ROOT / "meta.js"), str(ROOT / LANG_DIRS[lang] / "data.js")]
    out = subprocess.run([node_bin(), str(TOOLS / "dump_data.js"), *files],
                         capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"{LANG_DIRS[lang] or ''}data.js 讀不出來：{out.stderr.strip().splitlines()[-1] if out.stderr.strip() else '不明錯誤'}")
    return json.loads(out.stdout)


# ---------- 內容合約 ----------
def nonempty(x):
    return isinstance(x, str) and x.strip() != ""


def contract(w, lang):
    """每座島、樹幹、王冠島必須有的東西。回傳錯誤清單（字串）。"""
    errs = []
    tag = f"[{lang}]"
    isl = w.get("ISLANDS")
    if not isinstance(isl, list) or not isl:
        return [f"{tag} 沒有 ISLANDS"]
    ids = [d.get("id") for d in isl]
    if ids != list(range(1, len(isl) + 1)):
        errs.append(f"{tag} 島號要從 1 連續編到 {len(isl)}，現在是 {ids}（解鎖規則是「過了上一座島才開下一座」）")
    finals = [d.get("id") for d in isl if d.get("final")]
    if finals != [isl[-1].get("id")]:
        errs.append(f"{tag} 畢業島（final: true）要剛好一座、而且放最後，現在是 {finals}")
    for k in ("name", "boss", "badge", "stage", "topic", "core"):
        for d in isl:
            if not nonempty(d.get(k)):
                errs.append(f"{tag} 第 {d.get('id')} 島缺 {k}")
    for d in isl:
        if d.get("final"):
            continue
        p = f"{tag} 第 {d['id']} 島"
        pz = d.get("puzzle") or {}
        if not nonempty(pz.get("text")) or len(pz.get("options") or []) < 2:
            errs.append(f"{p} P1 謎題缺題目或選項")
        elif not (isinstance(pz.get("answer"), int) and 0 <= pz["answer"] < len(pz["options"])):
            errs.append(f"{p} P1 謎題的答案編號 {pz.get('answer')} 不在選項範圍內")
        if not d.get("principle"):
            errs.append(f"{p} P2 沒有原理")
        if len(d.get("chain") or []) < 3:
            errs.append(f"{p} P2 因果鏈少於 3 步")
        lab = d.get("lab") or {}
        if not nonempty(lab.get("goal")) or not lab.get("steps") or not lab.get("prompts"):
            errs.append(f"{p} P3 實驗缺目標、步驟或提示詞")
        for k, label in (("feynman", "P4 費曼題"), ("analogyHint", "P5 類比提示"), ("swan", "黑天鵝")):
            if not nonempty(d.get(k)):
                errs.append(f"{p} 缺 {label}")
        quiz = d.get("quiz") or []
        if len(quiz) != 4:
            errs.append(f"{p} 抽問要剛好 4 題（畫面寫「4 題答對 3 題」），現在 {len(quiz)} 題")
        for i, q in enumerate(quiz, 1):
            if not nonempty(q.get("q")) or len(q.get("opts") or []) < 2:
                errs.append(f"{p} 抽問第 {i} 題缺題目或選項")
            elif not (isinstance(q.get("a"), int) and 0 <= q["a"] < len(q["opts"])):
                errs.append(f"{p} 抽問第 {i} 題答案編號不在範圍內")
            if not nonempty(q.get("why")):
                errs.append(f"{p} 抽問第 {i} 題沒有「為什麼」（本課程不收只有答案的題目）")
        bosses = d.get("bosses") or []
        if len(bosses) < 2:
            errs.append(f"{p} Boss 案例少於 2 個（第 2 個是答錯後補打用）")
        for i, b in enumerate(bosses, 1):
            if not nonempty(b.get("text")) or len(b.get("opts") or []) < 2:
                errs.append(f"{p} Boss 第 {i} 案缺題目或選項")
            elif not (isinstance(b.get("a"), int) and 0 <= b["a"] < len(b["opts"])):
                errs.append(f"{p} Boss 第 {i} 案答案編號不在範圍內")
            if not nonempty(b.get("why")):
                errs.append(f"{p} Boss 第 {i} 案沒有「為什麼」")
    extra = w.get("CARD_EXTRA") or {}
    valid = {str(d.get("id")) for d in isl}
    for k, v in extra.items():
        if k not in valid:
            errs.append(f"{tag} CARD_EXTRA 有不存在的島 {k}")
        for j, u in enumerate((v or {}).get("update") or [], 1):
            if not nonempty(u):
                errs.append(f"{tag} 第 {k} 島補充第 {j} 條是空的")
    for d in isl:
        if not d.get("final") and not nonempty((extra.get(str(d["id"])) or {}).get("symptom")):
            errs.append(f"{tag} 第 {d['id']} 島沒有症狀（CARD_EXTRA.symptom，航海圖「壞了才抽」靠它）")
    for k in ("FINAL_ROUNDS", "FINAL_RUBRIC", "UI0", "TRUNK"):
        if not w.get(k):
            errs.append(f"{tag} 沒有 {k}")
    rub = w.get("FINAL_RUBRIC") or []
    if rub and sum(r[1] for r in rub) != 100:
        errs.append(f"{tag} 畢業評分表權重加起來是 {sum(r[1] for r in rub)}，要是 100")
    t = w.get("TRUNK") or {}
    for i, e in enumerate(t.get("exam") or [], 1):
        if not (isinstance(e.get("layer"), int) and 0 <= e["layer"] < len(t.get("layers") or [])):
            errs.append(f"{tag} 樹幹畢業考第 {i} 題的層次編號不對")
    return errs


def meta_contract(w):
    errs = []
    ver = w.get("CONTENT_VERSION")
    try:
        dt.date.fromisoformat(ver or "")
    except ValueError:
        errs.append(f"[meta] CONTENT_VERSION 要是日期（YYYY-MM-DD），現在是 {ver!r}")
    if not nonempty(w.get("REPO")) or "/" not in (w.get("REPO") or ""):
        errs.append("[meta] REPO 要寫成「帳號/倉庫」，回報按鈕靠它開 issue")
    fr = w.get("FRESHNESS") or {}
    ids = [str(d["id"]) for d in w.get("ISLANDS") or []] + ["trunk"]
    today = dt.date.today()
    for k in ids:
        e = fr.get(k)
        if not e:
            errs.append(f"[meta] FRESHNESS 沒有 {k}（每座島都要記上次驗證日）")
            continue
        for f in ("checked", "changed"):
            try:
                d = dt.date.fromisoformat(e.get(f) or "")
                if d > today:
                    errs.append(f"[meta] FRESHNESS[{k}].{f} 是未來的日期 {d}")
            except ValueError:
                errs.append(f"[meta] FRESHNESS[{k}].{f} 要是日期，現在是 {e.get(f)!r}")
        if not isinstance(e.get("watch", []), list):
            errs.append(f"[meta] FRESHNESS[{k}].watch 要是清單")
    for k in fr:
        if k not in ids:
            errs.append(f"[meta] FRESHNESS 有不存在的島 {k}")
    try:
        if max(fr[k]["changed"] for k in fr) > ver:
            errs.append(f"[meta] 有島的 changed 比 CONTENT_VERSION（{ver}）新：改了內容要一起把 CONTENT_VERSION 更新")
    except (KeyError, TypeError, ValueError):
        pass
    return errs


# ---------- 四語對齊 ----------
def shape_diff(a, b, path, out):
    """a 是繁中、b 是譯本。結構要一樣：同樣的欄位、清單一樣長、數字（答案編號、島號）一樣、字串不能是空的。"""
    if isinstance(a, dict):
        if not isinstance(b, dict):
            out.append(f"{path} 應該是物件"); return
        ka = set(a) - ZH_ONLY_KEYS
        kb = set(b) - ZH_ONLY_KEYS
        for k in sorted(ka - kb):
            out.append(f"{path}.{k} 譯本沒有")
        for k in sorted(kb - ka):
            out.append(f"{path}.{k} 繁中沒有，譯本多出來")
        for k in sorted(ka & kb):
            shape_diff(a[k], b[k], f"{path}.{k}", out)
    elif isinstance(a, list):
        if not isinstance(b, list):
            out.append(f"{path} 應該是清單"); return
        if len(a) != len(b):
            out.append(f"{path} 繁中 {len(a)} 項、譯本 {len(b)} 項"); return
        for i, (x, y) in enumerate(zip(a, b)):
            shape_diff(x, y, f"{path}[{i}]", out)
    elif isinstance(a, bool) or isinstance(a, (int, float)):
        if a != b:
            out.append(f"{path} 繁中是 {a}、譯本是 {b}（答案編號或島號要一樣）")
    elif isinstance(a, str):
        if not isinstance(b, str):
            out.append(f"{path} 應該是文字")
        elif a.strip() and not b.strip():
            out.append(f"{path} 譯本是空的")


CONTENT_KEYS = ["ISLANDS", "FINAL_ROUNDS", "FINAL_RUBRIC", "UI0", "CARD_EXTRA", "TRUNK"]


def parity(zh, other, lang):
    out = []
    for k in CONTENT_KEYS:
        shape_diff(zh.get(k), other.get(k), k, out)
    return [f"[{lang}] 跟繁中不對齊：{x}" for x in out]


# ---------- 翻譯有沒有跟上 ----------
def leaves(x, path=""):
    if isinstance(x, dict):
        for k in sorted(x):
            if k not in ZH_ONLY_KEYS:
                yield from leaves(x[k], f"{path}.{k}" if path else k)
    elif isinstance(x, list):
        for i, y in enumerate(x):
            yield from leaves(y, f"{path}[{i}]")
    elif isinstance(x, str):
        yield path, x


def fingerprint(zh):
    fp = {}
    for k in CONTENT_KEYS:
        for p, s in leaves(zh.get(k), k):
            fp[p] = hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]
    return fp


def i18n_drift(zh):
    """繁中哪些句子在英日上次同步之後改過（或是新加的）。"""
    lock = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {}
    fp = fingerprint(zh)
    drift = {}
    for lang in TRANSLATED:
        old = lock.get(lang)
        if old is None:
            drift[lang] = None  # 還沒有同步紀錄
            continue
        changed = [p for p, h in fp.items() if old.get(p) != h]
        drift[lang] = changed
    return drift


def accept_i18n(zh, langs):
    lock = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {}
    fp = fingerprint(zh)
    for lang in langs:
        lock[lang] = fp
    LOCK.write_text(json.dumps(lock, ensure_ascii=False, indent=0, sort_keys=True) + "\n", encoding="utf-8")


# ---------- 產生檔是不是最新 ----------
def opencc_python():
    """找一個裝了 opencc 的 Python（簡體版要用）。找不到回傳 None。"""
    local = {}
    try:  # 本機設定（不進版控）：.evolve/local.json 的 {"opencc_python": "..."}
        local = json.loads((ROOT / ".evolve" / "local.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    cands = [os.environ.get("OPENCC_PYTHON"), local.get("opencc_python"), sys.executable, "python3"]
    for c in cands:
        if not c or not shutil.which(c) and not pathlib.Path(c).exists():
            continue
        r = subprocess.run([c, "-c", "import opencc"], capture_output=True)
        if r.returncode == 0:
            return c
    return None


def run_builders():
    """依序執行產生腳本。回傳 (錯誤清單, 這次沒查到清單)。"""
    errs, skipped = [], []
    py = opencc_python()
    for b in BUILDERS:
        exe = sys.executable
        if b == "build_zh_hans.py":
            if not py:
                skipped.append("簡體版：這台電腦找不到裝了 opencc 的 Python（設環境變數 OPENCC_PYTHON，或寫在 .evolve/local.json 的 opencc_python）")
                continue
            exe = py
        r = subprocess.run([exe, str(TOOLS / b)], capture_output=True, text=True, cwd=ROOT, timeout=300)
        if r.returncode != 0:
            msg = (r.stderr or r.stdout).strip().splitlines()
            errs.append(f"[產生] {b} 失敗：" + (" / ".join(msg[-4:]) if msg else "不明錯誤"))
    return errs, skipped


def generated_fresh():
    """重新產生一次，跟倉庫裡的比。檢查完把檔案放回原樣，不留副作用。"""
    before = {g: (ROOT / g).read_bytes() if (ROOT / g).exists() else None for g in GENERATED}
    errs, skipped = run_builders()
    stale = []
    for g in GENERATED:
        now = (ROOT / g).read_bytes() if (ROOT / g).exists() else None
        if now != before[g]:
            stale.append(g)
            if before[g] is None:
                (ROOT / g).unlink()
            else:
                (ROOT / g).write_bytes(before[g])
    if stale:
        errs.append("[產生] 這些檔不是最新的，請執行 python3 tools/build_all.py 再提交：" + "、".join(stale))
    return errs, skipped


# ---------- 該重新驗證 ----------
def freshness(meta, isl_names):
    today = dt.date.today()
    due = []
    for k, e in (meta.get("FRESHNESS") or {}).items():
        try:
            checked = dt.date.fromisoformat(e["checked"])
        except (KeyError, ValueError):
            continue
        age = (today - checked).days
        limit = STALE_DAYS_WATCH if e.get("watch") else STALE_DAYS_OTHER
        if age > limit:
            due.append({"island": k, "name": isl_names.get(k, k), "checked": e["checked"], "age_days": age,
                        "limit_days": limit, "watch": e.get("watch") or []})
    return sorted(due, key=lambda x: -x["age_days"])


# ---------- 主程式 ----------
def run_all(check_generated=True):
    res = {"errors": [], "skipped": [], "drift": {}, "due": [], "content_version": None, "islands": 0}
    if not node_bin():
        res["errors"].append("找不到 node：讀不了 data.js，這次什麼都沒查到")
        return res, None
    data = {}
    for lang in LANG_DIRS:
        try:
            data[lang] = load(lang)
        except RuntimeError as e:
            res["errors"].append(str(e))
    zh = data.get("zh")
    if not zh:
        return res, None
    res["content_version"] = zh.get("CONTENT_VERSION")
    res["islands"] = len(zh.get("ISLANDS") or [])
    res["errors"] += meta_contract(zh)
    for lang, w in data.items():
        res["errors"] += contract(w, lang)
    for lang in ("zh-hans", *TRANSLATED):
        if lang in data:
            res["errors"] += parity(zh, data[lang], lang)
    res["drift"] = i18n_drift(zh)
    for lang, paths in res["drift"].items():
        if paths is None:
            res["errors"].append(f"[{lang}] 還沒有翻譯同步紀錄：譯本對齊後執行 python3 tools/check.py --accept-i18n {lang}")
        elif paths:
            sample = "、".join(paths[:8]) + ("……" if len(paths) > 8 else "")
            res["errors"].append(f"[{lang}] 繁中有 {len(paths)} 句在上次同步後改過，譯本要跟著改：{sample}"
                                 f"（改好後執行 python3 tools/check.py --accept-i18n {lang}）")
    names = {str(d["id"]): d["name"] for d in zh.get("ISLANDS") or []}
    names["trunk"] = (zh.get("TRUNK") or {}).get("name", "樹幹")
    res["due"] = freshness(zh, names)
    if check_generated:
        e, s = generated_fresh()
        res["errors"] += e
        res["skipped"] += s
    return res, zh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--accept-i18n", nargs="*", metavar="LANG")
    ap.add_argument("--no-generated", action="store_true", help="略過「產生檔是不是最新」（較快）")
    a = ap.parse_args()

    if a.accept_i18n is not None:
        langs = a.accept_i18n or TRANSLATED
        bad = [x for x in langs if x not in TRANSLATED]
        if bad:
            sys.exit(f"只能是 {TRANSLATED}，收到 {bad}")
        res, zh = run_all(check_generated=False)
        par = [e for e in res["errors"] if any(e.startswith(f"[{x}] 跟繁中不對齊") for x in langs)]
        if zh is None or par:
            sys.exit("譯本結構還沒對齊，不能記成已同步：\n" + "\n".join(par or res["errors"]))
        accept_i18n(zh, langs)
        print(f"已記錄：{'、'.join(langs)} 跟目前的繁中內容同步")
        return

    res, _ = run_all(check_generated=not a.no_generated)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print(f"內容版本 {res['content_version']}，{res['islands']} 座島")
        if res["errors"]:
            print(f"\n錯誤 {len(res['errors'])} 項：")
            for e in res["errors"]:
                print("  ✗ " + e)
        else:
            print("錯誤 0 項")
        if res["skipped"]:
            print("\n這次沒查到（不算通過）：")
            for s in res["skipped"]:
                print("  ? " + s)
        if res["due"]:
            print(f"\n該重新驗證 {len(res['due'])} 座（待辦，不算錯誤）：")
            for d in res["due"]:
                print(f"  · {d['name']}：上次驗證 {d['checked']}（{d['age_days']} 天前，期限 {d['limit_days']} 天）" +
                      (f"，要看：{'；'.join(d['watch'])}" if d["watch"] else ""))
    sys.exit(1 if res["errors"] else 0)


if __name__ == "__main__":
    main()
