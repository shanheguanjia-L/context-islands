"""體檢工具的測試：確定它真的擋得住壞內容（只用標準函式庫，不連網）。

執行：python3 -m unittest discover -s tests
"""
import copy
import datetime as dt
import json
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock

TOOLS = pathlib.Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))
import board  # noqa: E402
import check  # noqa: E402


def island(i, final=False):
    d = {"id": i, "name": f"島{i}", "boss": "怪", "badge": "章", "stage": "探索", "topic": "主題", "core": "核心"}
    if final:
        d["final"] = True
        return d
    d.update({
        "puzzle": {"text": "題", "options": ["a", "b"], "answer": 1},
        "principle": ["原理"], "chain": ["一", "二", "三"],
        "lab": {"goal": "目標", "steps": ["步"], "prompts": ["提示"]},
        "feynman": "費曼", "analogyHint": "類比", "swan": "黑天鵝",
        "quiz": [{"q": "問", "opts": ["a", "b"], "a": 0, "why": "因為"} for _ in range(4)],
        "bosses": [{"text": "案", "opts": ["a", "b"], "a": 1, "why": "因為"} for _ in range(2)],
    })
    return d


def course():
    return {
        "ISLANDS": [island(1), island(2), island(3, final=True)],
        "CARD_EXTRA": {"1": {"symptom": "症狀"}, "2": {"symptom": "症狀", "update": ["補充"]}},
        "FINAL_ROUNDS": [{"title": "t", "fields": [["a", "b"]]}],
        "FINAL_RUBRIC": [["x", 60, "y"], ["z", 40, "w"]],
        "UI0": {"dot": "・"},
        "TRUNK": {"layers": [{"name": "一"}, {"name": "二"}], "exam": [{"layer": 1}]},
        "CONTENT_VERSION": "2026-11-27", "REPO": "a/b",
        "FRESHNESS": {k: {"checked": "2026-11-27", "changed": "2026-11-27", "watch": []} for k in ("trunk", "1", "2", "3")},
    }


class Contract(unittest.TestCase):
    def test_good_course_passes(self):
        self.assertEqual(check.contract(course(), "zh"), [])
        self.assertEqual(check.meta_contract(course()), [])

    def test_missing_why_is_blocked(self):
        c = course()
        c["ISLANDS"][0]["bosses"][1]["why"] = " "
        errs = check.contract(c, "zh")
        self.assertTrue(any("Boss 第 2 案沒有「為什麼」" in e for e in errs), errs)

    def test_answer_out_of_range(self):
        c = course()
        c["ISLANDS"][1]["quiz"][2]["a"] = 5
        self.assertTrue(any("抽問第 3 題答案編號" in e for e in check.contract(c, "zh")))

    def test_quiz_must_be_four(self):
        c = course()
        c["ISLANDS"][0]["quiz"].pop()
        self.assertTrue(any("抽問要剛好 4 題" in e for e in check.contract(c, "zh")))

    def test_ids_and_final_position(self):
        c = course()
        c["ISLANDS"][0], c["ISLANDS"][2] = c["ISLANDS"][2], c["ISLANDS"][0]
        errs = check.contract(c, "zh")
        self.assertTrue(any("島號要從 1 連續" in e for e in errs))
        self.assertTrue(any("畢業島" in e for e in errs))

    def test_new_island_needs_symptom_and_freshness(self):
        c = course()
        c["ISLANDS"].insert(2, island(3))
        c["ISLANDS"][3]["id"] = 4
        errs = check.contract(c, "zh") + check.meta_contract(c)
        self.assertTrue(any("第 3 島沒有症狀" in e for e in errs), errs)
        self.assertTrue(any("FRESHNESS 沒有 4" in e for e in errs), errs)

    def test_changed_newer_than_version(self):
        c = course()
        c["FRESHNESS"]["1"]["changed"] = "2026-11-28"
        c["FRESHNESS"]["1"]["checked"] = "2026-11-20"
        with mock.patch.object(check.dt, "date", wraps=dt.date) as d:
            d.today.return_value = dt.date(2026, 12, 1)
            errs = check.meta_contract(c)
        self.assertTrue(any("CONTENT_VERSION" in e for e in errs), errs)


class Parity(unittest.TestCase):
    def test_same_shape_passes(self):
        self.assertEqual(check.parity(course(), course(), "en"), [])

    def test_answer_moved_is_caught(self):
        en = course()
        en["ISLANDS"][0]["bosses"][0]["a"] = 0
        out = check.parity(course(), en, "en")
        self.assertTrue(any("ISLANDS[0].bosses[0].a" in e for e in out), out)

    def test_missing_option_and_empty_text(self):
        en = course()
        en["ISLANDS"][1]["quiz"][0]["opts"].pop()
        en["ISLANDS"][0]["swan"] = ""
        out = "\n".join(check.parity(course(), en, "en"))
        self.assertIn("ISLANDS[1].quiz[0].opts 繁中 2 項、譯本 1 項", out)
        self.assertIn("ISLANDS[0].swan 譯本是空的", out)

    def test_zh_only_keys_ignored(self):
        zh = course()
        zh["ISLANDS"][0]["fixes"] = "內部標記"
        self.assertEqual(check.parity(zh, course(), "en"), [])


class Drift(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.patch = mock.patch.object(check, "LOCK", self.tmp / "lock.json")
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        shutil.rmtree(self.tmp)

    def test_no_lock_reports_none(self):
        self.assertEqual(check.i18n_drift(course()), {"en": None, "ja": None})

    def test_changed_sentence_is_listed(self):
        zh = course()
        check.accept_i18n(zh, ["en", "ja"])
        self.assertEqual(check.i18n_drift(zh), {"en": [], "ja": []})
        zh2 = copy.deepcopy(zh)
        zh2["ISLANDS"][1]["bosses"][0]["why"] = "改過的理由"
        d = check.i18n_drift(zh2)
        self.assertEqual(d["en"], ["ISLANDS[1].bosses[0].why"])
        check.accept_i18n(zh2, ["en"])
        d = check.i18n_drift(zh2)
        self.assertEqual(d["en"], [])
        self.assertEqual(d["ja"], ["ISLANDS[1].bosses[0].why"])


class Freshness(unittest.TestCase):
    def test_watch_islands_go_stale_sooner(self):
        c = course()
        c["FRESHNESS"]["1"] = {"checked": "2026-01-01", "changed": "2026-01-01", "watch": ["工具"]}
        c["FRESHNESS"]["2"] = {"checked": "2026-01-01", "changed": "2026-01-01", "watch": []}
        with mock.patch.object(check.dt, "date", wraps=dt.date) as d:
            d.today.return_value = dt.date(2026, 6, 1)
            due = check.freshness(c, {"1": "島1", "2": "島2"})
        self.assertEqual([x["island"] for x in due], ["1"])


class Board(unittest.TestCase):
    def test_nothing_to_do(self):
        self.assertEqual(board.render({"errors": [], "due": [], "skipped": []}), "NOTHING_TO_DO")

    def test_lists_due(self):
        out = board.render({"errors": [], "skipped": [], "content_version": "2026-11-27", "islands": 12,
                            "due": [{"name": "工具港", "checked": "2026-01-01", "age_days": 200, "watch": ["MCP"]}]})
        self.assertIn("**工具港**", out)
        self.assertIn("MCP", out)


@unittest.skipUnless(shutil.which("node"), "沒有 node")
class RealCourse(unittest.TestCase):
    """真正的課程資料也要過合約與四語對齊（不含產生檔比對，那個在 CI 由 check.py 做）。"""

    def test_real_data(self):
        res, zh = check.run_all(check_generated=False)
        self.assertEqual(res["errors"], [], "\n".join(res["errors"]))
        self.assertGreaterEqual(res["islands"], 12)
        json.dumps(res)


if __name__ == "__main__":
    unittest.main()
