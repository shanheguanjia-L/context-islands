"""演化引擎的關卡測試（不呼叫 AI、不連網）。"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))
import evolve  # noqa: E402


class Gate(unittest.TestCase):
    def test_first_line_keeps_full_name(self):
        out = " M index.html\n M data.js\n?? 更新紀錄.md\nR  old.js -> tools/new.py"
        self.assertEqual(evolve.touched_files(out), ["index.html", "data.js", "更新紀錄.md", "tools/new.py"])

    def test_code_and_ci_are_forbidden(self):
        bad = evolve.forbidden(["index.html", "data.js", "tools/check.py", "tools/i18n.lock.json", ".github/workflows/x.yml", "meta.js"])
        self.assertEqual(bad, ["index.html", "tools/check.py", ".github/workflows/x.yml"])


if __name__ == "__main__":
    unittest.main()
