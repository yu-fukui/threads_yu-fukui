"""12月の 20:00 を、美容のかわりに福井のふるさと納税の紹介にする（AI は使わない）。

2026-11-23 統括決定（代表「YU アカウントはアフィリエイトを伸ばす施策を」）：
  - 20時の美容は閲覧が約10、28日で押されたのは2回。ふるさと納税は 12/31 が締め切りで12月がいちばん動く
  - 福井の返礼品を1日1本。困りごとから入る型（ドパガキ）、本文は日付から、最後に空行と「PR」
  - 事実は楽天の商品情報（返礼品のリスト）だけ。リンクは返信に。返信の最後にも空行と「PR」
  - 1月からは 20時を福井の宿◯選にする（別に作る）

返礼品のリストと切り口は scripts/ふるさと納税.py（福井のおでかけと同じもの。リストは X のリポジトリ）。
福井のおでかけの 22時 と同じ日に同じ品が並ばないよう、日をずらして選び、直近14日に yu で出した品は後ろへ回す。

  python scripts/年末のふるさと.py          （TARGET_DATE・DRY_RUN は compose.py と同じ）
"""
from __future__ import annotations

import json
import os
import random
import string
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ふるさと納税 as 寄付  # noqa: E402

# 品は最初に当たった切り口にだけ入れる（「浜焼き鯖」が「焼」で手仕事に入らないよう、先の「若狭の海のもの」に）
寄付.先に当たった切り口だけ = True
# お米の切り口に、米を使った調味料・お酒・お菓子を入れない（「特別栽培米で作った純米酢」がお米に入った）
for _き in 寄付.切り口たち:
    if _き.get("名") == "コシヒカリの生まれた土地":
        _き["除く語"] = [*_き.get("除く語", []), "酢", "みりん", "酒", "せんべい", "煎餅", "あられ", "麹", "糀"]
# 見出しの言い方を、並ぶ品に合わせる（「若狭湾から届くもの」に坂井市の甘えび・越前町のほたるいかが並んだ）
for _き in 寄付.切り口たち:
    if _き.get("名") == "若狭の海のもの":
        _き["問い"] = "福井の港町から届く海のもの"
    elif _き.get("名") == "福井の畑のもの":
        _き["問い"] = "福井の畑のもの"
嶺南 = ("敦賀市", "美浜町", "若狭町", "小浜市", "おおい町", "高浜町")
# 一言（フック）は、並べた品に合うときだけ出す（手仕事の回に、めがねが無いのにめがねの一言が出ないように）
フックに要る語 = {
    "福井の職人がつくるもの": ["めがね", "眼鏡", "メガネ", "フレーム"],
    "福井の人が食べているもの": ["羽二重", "水ようかん", "水羊かん"],
    "福井の畑のもの": ["梅", "里芋", "さといも"],
}

JST = ZoneInfo("Asia/Tokyo")
QUEUE = Path("posts/queue.jsonl")
上限 = 500
時 = 20
始め, 終わり = date(2026, 12, 1), date(2026, 12, 31)
印 = "ふるさと納税（年末）"
曜 = "月火水木金土日"


def 期間か(日: date) -> bool:
    return 始め <= 日 <= 終わり


def _行たち() -> list[dict]:
    if not QUEUE.exists():
        return []
    出 = []
    for l in QUEUE.read_text(encoding="utf-8").splitlines():
        if l.strip() and not l.startswith("#"):
            try:
                出.append(json.loads(l))
            except json.JSONDecodeError:
                pass
    return 出


def 出した品(行たち: list[dict], 品たち: list[dict], 日: date) -> set[str]:
    """直近14日に yu で出した品（見せる名）。"""
    名 = {寄付.見せる名(p): p for p in 品たち}
    出 = set()
    for e in 行たち:
        at = str(e.get("scheduled_at", ""))[:10]
        if not at or 印 not in str(e.get("note") or ""):
            continue
        try:
            d = datetime.strptime(at, "%Y-%m-%d").date()
        except ValueError:
            continue
        if 0 < (日 - d).days <= 14:
            文 = "\n".join([str(e.get("text") or ""), *(e.get("thread") or [])])
            出 |= {n for n in 名 if n and n in 文}
    return 出


def 本文(日: date, まとめ: dict) -> str:
    き = まとめ["切り口"]
    一覧 = "\n".join(寄付.一覧の行(まとめ))
    要る = フックに要る語.get(き.get("名"), [])
    名たち = " ".join(str(p.get("名") or "") for p in まとめ["品"])
    フック = f"{き.get('フック')}\n" if き.get("フック") and (not 要る or any(w in 名たち for w in 要る)) else ""
    if き.get("名") == "若狭の海のもの" and not all(str(p.get("自治体")) in 嶺南 for p in まとめ["品"]):
        フック = ""  # 鯖街道の一言は、若狭の品だけが並ぶときに
    残り = (終わり - 日).days
    締め = "今日が年内の締め切りです。" if 残り == 0 else f"年内の締め切りまで、あと{残り}日。"
    return (
        f"{日.month}月{日.day}日（{曜[日.weekday()]}）。{締め}\n"
        "ふるさと納税、何にするか決めきれていない人へ。\n"
        "\n"
        f"【福井】{き['問い']}を{len(まとめ['品'])}つ。\n"
        "\n"
        f"{一覧}\n"
        "\n"
        f"{フック}"
        "その年の控除の対象になるのは、12月31日までの寄付です。\n"
        "\n"
        "PR"
    )


def 返信(まとめ: dict) -> list[str]:
    """返礼品ごとの一行とリンク。500字に収まる分ずつまとめ、それぞれの最後に空行と PR。"""
    出, 今 = [], ""
    for 行 in 寄付.返信の行(まとめ):
        足す = (今 + "\n\n" + 行) if 今 else 行
        if len(足す) + len("\n\nPR") > 上限 and 今:
            出.append(今 + "\n\nPR")
            今 = 行
        else:
            今 = 足す
    if 今:
        出.append(今 + "\n\nPR")
    return 出


def 組み立てる(日: date, 品たち: list[dict], 避ける: set[str]) -> dict | None:
    # 福井のおでかけ（22時）は同じリスト・同じ計算で選ぶので、日をずらして別の切り口・別の品にする
    まとめ = 寄付.今日のまとめ(日 + timedelta(days=17), 品たち, いくつ=3, 避ける=避ける)
    if not まとめ or len(まとめ["品"]) < 3:
        return None
    文 = 本文(日, まとめ)
    返 = 返信(まとめ)
    if len(文) > 上限 or any(len(x) > 上限 for x in 返) or not all("http" in x for x in 返):
        return None
    印字 = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return {
        "id": f"p-{日:%Y%m%d}{時:02d}-{印字}",
        "text": 文,
        "scheduled_at": f"{日.isoformat()}T{時:02d}:00:00+09:00",
        "thread": 返,
        "note": f"{印}／{まとめ['切り口'].get('名')}"[:120],
    }


def 対象日() -> date:
    t = os.environ.get("TARGET_DATE", "").strip()
    if t:
        return datetime.strptime(t, "%Y-%m-%d").date()
    return (datetime.now(JST) + timedelta(days=1)).date()


def main() -> None:
    日 = 対象日()
    if not 期間か(日):
        print(f"{日} は年末のふるさと納税の期間（{始め}〜{終わり}）ではありません。何もしません。")
        return
    行たち = _行たち()
    if any(str(e.get("scheduled_at", "")).startswith(f"{日.isoformat()}T{時:02d}:00") for e in 行たち):
        print(f"{日} {時}:00 はすでに埋まっています。")
        return
    品たち = 寄付.読む()
    if not 品たち:
        print("::warning::ふるさと納税の返礼品のリストが読めません。作りません。")
        return
    投稿 = 組み立てる(日, 品たち, 出した品(行たち, 品たち, 日))
    if not 投稿:
        print(f"::warning::{日} {時}:00 のふるさと納税の投稿は作れませんでした。")
        return
    print(f"=== {時}:00 ふるさと納税 ({len(投稿['text'])} 字) ===\n{投稿['text']}")
    for t in 投稿["thread"]:
        print(f"--- 返信 ---\n{t}")
    if os.environ.get("DRY_RUN", "").lower() == "true":
        print("DRY_RUN のため、キューには書き込みません。")
        return
    with QUEUE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(投稿, ensure_ascii=False) + "\n")
    print("キューにふるさと納税の投稿を1本足しました。")


if __name__ == "__main__":
    main()
