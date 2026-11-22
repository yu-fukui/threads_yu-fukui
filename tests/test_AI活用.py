import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import importlib

m = importlib.import_module("AI活用の投稿")


class 検査のテスト(unittest.TestCase):
    def test_通る(self):
        self.assertEqual(m.検査("AI に任せたら、上限を考える分で使い切って本文が0本になった。上限と考える量を渡して直した。仕様と同様に動く。"), [])

    def test_止める(self):
        for 文 in ["今月は $12 かかった", "1,200円で", "sk-abcdefghijk を入れる", "a@example.com に送る",
                   "https://example.com", "申込番号を照らす", "田中様の申し込み", "必見の方法", "x" * 500]:
            self.assertTrue(m.検査(文), 文)

    def test_材料から危ない行を落とす(self):
        s = m.材料をきれいにする("直した\n料金は $5\nCo-Authored-By: x\nhttps://x\n上限を渡す")
        self.assertEqual(s, "直した\n上限を渡す")

    def test_JSON(self):
        self.assertEqual(m.JSONを取り出す('前置き {"A": [{"本文": "x"}]} 後'), {"A": [{"本文": "x"}]})


if __name__ == "__main__":
    unittest.main()
