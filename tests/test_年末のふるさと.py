import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import 年末のふるさと as m  # noqa: E402


class 年末のふるさとのテスト(unittest.TestCase):
    def test_期間(self):
        self.assertFalse(m.期間か(date(2026, 11, 30)))
        self.assertTrue(m.期間か(date(2026, 12, 1)))
        self.assertTrue(m.期間か(date(2026, 12, 31)))
        self.assertFalse(m.期間か(date(2027, 1, 1)))

    def test_本文は日付から始まりPRで終わる(self):
        まとめ = {"切り口": {"名": "x", "問い": "福井のお米", "フック": ""},
                  "品": [{"名": "米A", "自治体": "福井市"}, {"名": "米B", "自治体": "大野市"}, {"名": "米C", "自治体": "小浜市"}]}
        文 = m.本文(date(2026, 12, 3), まとめ)
        self.assertTrue(文.startswith("12月3日（木）"))
        self.assertTrue(文.endswith("\n\nPR"))
        self.assertNotIn("節税", 文)

    def test_返信はそれぞれPRで終わる(self):
        まとめ = {"切り口": {"名": "x", "問い": "q"},
                  "品": [{"名": f"品{i}", "自治体": "福井市", "url": "https://example.com/" + "a" * 200} for i in range(3)]}
        for x in m.返信(まとめ):
            self.assertTrue(x.endswith("\n\nPR"))
            self.assertLessEqual(len(x), 500)


if __name__ == "__main__":
    unittest.main()
