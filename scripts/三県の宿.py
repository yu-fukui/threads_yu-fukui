"""yu の宿の投稿を1日3本作る（7時・13時・15時。福井・石川・ぎふあいちの宿を回す）。

2026-11-03 代表「宿を1日3回にして、福井だけでなく石川・ぎふあいちの宿も紹介して。美容は減らす」
時間割の案に代表「はい」（統括 11/3）：
  - 7時・13時・15時に宿。どの地域をどの時間に出すかは日ごとに回す（時間の差と地域の差を分けて見るため）
  - 形は yu の◯選（見出し＋「① 絵 宿名（市町）」、返信に一言とリンク、本文と返信の最後に PR）
  - 15時の「3アカウントで同じ内容を比べる」はやめる。yu は地域のアカウントがその日に出す・出した宿を外して選ぶ
  - 14日の決まりは yu の3本をまとめて見る（14日以内に yu で出した宿は、どの地域の分でも選ばない）
  - AI は使わない（宿のリスト＝楽天トラベルの API で取った事実だけで組み立てる）

宿のリスト・土地の切り口は、各地域のものを読む（scripts/県の宿.py は福井のおでかけの scripts/宿.py と同じもの）。
  福井 … X のリポジトリの neta/宿.jsonl（短いリンクあり）
  石川・ぎふあいち … 各リポジトリの region.json と neta/宿.jsonl（短いリンクは無いので、返信が2本に分かれることがある）

  python scripts/三県の宿.py          （TARGET_DATE・DRY_RUN は compose.py と同じ）
"""
from __future__ import annotations

import importlib.util
import json
import os
import random
import string
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
QUEUE = Path("posts/queue.jsonl")
上限 = 500
印 = "宿（三県）"
時刻 = (7, 13, 15)
起点 = date(2026, 11, 5)   # この日を ぎふあいち 7時・石川 13時・福井 15時 にする（統括へ出した案のとおり）
RAW = "https://raw.githubusercontent.com/"

# 地域：名前・region.json と宿のリストの置き場・地域のアカウントの queue
地域たち = [
    {"名": "福井", "region": None, "宿": None, "queue": "fukui-fukui/threads"},
    {"名": "石川", "region": "yu-fukui/ishikawa-odekake", "宿": "yu-fukui/ishikawa-odekake",
     "queue": "yu-fukui/ishikawa-odekake"},
    {"名": "ぎふあいち", "region": "yu-fukui/gifu-aichi-odekake", "宿": "yu-fukui/gifu-aichi-odekake",
     "queue": "yu-fukui/gifu-aichi-odekake"},
]


def その日の割り当て(日: date) -> dict[int, dict]:
    """時刻 → 地域。日ごとに1つずつずらす。11/5 は 7時 ぎふあいち・13時 石川・15時 福井。"""
    ずれ = (日 - 起点).days % 3
    並び = [地域たち[2], 地域たち[1], 地域たち[0]]   # 起点の日の 7・13・15 時
    return {時: 並び[(i + ずれ) % 3] for i, 時 in enumerate(時刻)}


def _取る(repo: str, パス: str) -> str | None:
    url = f"{RAW}{repo}/main/{urllib.request.quote(パス)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "compose"})
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"::warning::{repo} の {パス} を読めませんでした（{e}）")
        return None


def 県の宿を読む(地: dict, 置き場: Path):
    """その地域の設定で scripts/県の宿.py を読み込んだモジュールを返す（読めなければ None）。"""
    region = 置き場 / f"{地['名']}_region.json"
    if 地["region"]:
        t = _取る(地["region"], "region.json")
        if t is None:
            return None
        region.write_text(t, encoding="utf-8")
    元 = os.environ.get("REGION_FILE")
    os.environ["REGION_FILE"] = str(region)   # 福井は無いファイル → 福井のまま（X のリポジトリのリストを読む）
    try:
        spec = importlib.util.spec_from_file_location(f"県の宿_{地['名']}", Path(__file__).resolve().parent / "県の宿.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
    finally:
        if 元 is None:
            os.environ.pop("REGION_FILE", None)
        else:
            os.environ["REGION_FILE"] = 元
    if 地["宿"]:
        t = _取る(地["宿"], "neta/宿.jsonl")
        if t is None:
            return None
        p = 置き場 / f"{地['名']}_宿.jsonl"
        p.write_text(t, encoding="utf-8")
        m.宿の置き場 = p
    else:
        m.宿の置き場 = 置き場 / "無い.jsonl"   # 手元に無い → https で X のリポジトリを読む
    return m


def _行たち(text: str | None) -> list[dict]:
    出 = []
    for l in (text or "").splitlines():
        l = l.strip()
        if l.startswith("{"):
            try:
                出.append(json.loads(l))
            except ValueError:
                pass
    return 出


def 文(e: dict) -> str:
    return "\n".join([str(e.get("text") or ""), *[str(t) for t in (e.get("thread") or [])]])


def 出ている宿(投稿たち: list[dict], 宿mod, 宿たち: list[dict], 始め: date, 終わり: date) -> set[str]:
    本文たち = [文(e) for e in 投稿たち if 始め.isoformat() <= str(e.get("scheduled_at") or "")[:10] <= 終わり.isoformat()]
    return {宿mod.見せる名(h) for h in 宿たち if any(宿mod.見せる名(h) in t for t in 本文たち)}


def 本文(宿mod, まとめ: dict) -> str:
    き = まとめ["切り口"]
    問い = str(き.get("問い") or き.get("名") or "").strip()
    見出し = f"【{宿mod.県名}】{問い}{len(まとめ['宿'])}選"
    return 見出し + "\n\n" + "\n".join(宿mod.一覧の行(まとめ)) + "\n\nPR"


def 返信(宿mod, まとめ: dict) -> list[str]:
    頭 = "楽天トラベルのページはこちらです"
    出, いま = [], 頭
    for 行 in 宿mod.返信の行(まとめ):
        つぎ = いま + "\n\n" + 行
        if len(つぎ + "\n\nPR") > 上限 and いま != 頭:
            出.append(いま)
            いま = 行
        else:
            いま = つぎ
    出.append(いま)
    return [x + "\n\nPR" for x in 出]


def 組み立てる(宿mod, 宿たち: list[dict], 日: date, 時: int, 避ける: set[str], 地名: str) -> dict | None:
    # 地域のアカウントは同じ日に同じ計算で切り口を選ぶので、yu は日をずらして別の切り口・別の並びにする
    # （地域の作成が yu より後に走っても、同じ宿が並ばないように）
    まとめ = 宿mod.今日のまとめ(日 + timedelta(days=11), 宿たち, いくつ=宿mod.今日の件数(日), 避ける=避ける)
    if not まとめ:
        return None
    まとめ = {**まとめ, "宿": [h for h in まとめ["宿"] if 宿mod.見せる名(h) not in 避ける]}
    if len(まとめ["宿"]) < 3:
        print(f"::warning::{日} {時}:00（{地名}）は、出していない宿が3軒そろいません。")
        return None
    # 本文が長いとき・返信が分かれるときは下から減らす（3軒まで）
    while (len(本文(宿mod, まとめ)) > 上限 or len(返信(宿mod, まとめ)) > 1) and len(まとめ["宿"]) > 3:
        まとめ = {**まとめ, "宿": まとめ["宿"][:-1]}
    if len(本文(宿mod, まとめ)) > 上限 or any(len(x) > 上限 for x in 返信(宿mod, まとめ)):
        return None
    短縮 = 宿mod.短縮を読む()
    if not all(宿mod.宿のリンク先(h, 短縮).startswith("http") for h in まとめ["宿"]):
        return None
    印字 = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return {
        "id": f"p-{日:%Y%m%d}{時:02d}-{印字}",
        "text": 本文(宿mod, まとめ),
        "scheduled_at": f"{日.isoformat()}T{時:02d}:00:00+09:00",
        "thread": 返信(宿mod, まとめ),
        "note": f"{印}／{地名}（{len(まとめ['宿'])}選・{まとめ['切り口'].get('名')}）"[:120],
    }


def 対象日() -> date:
    t = os.environ.get("TARGET_DATE", "").strip()
    if t:
        return datetime.strptime(t, "%Y-%m-%d").date()
    return (datetime.now(JST) + timedelta(days=1)).date()


def main() -> None:
    日 = 対象日()
    すでに = _行たち(QUEUE.read_text(encoding="utf-8")) if QUEUE.exists() else []
    足す = []
    with tempfile.TemporaryDirectory() as d:
        置き場 = Path(d)
        for 時, 地 in その日の割り当て(日).items():
            if any(str(e.get("scheduled_at", "")).startswith(f"{日.isoformat()}T{時:02d}:") for e in すでに + 足す):
                print(f"{日} {時}:00 はすでに埋まっています。")
                continue
            宿mod = 県の宿を読む(地, 置き場)
            宿たち = 宿mod.読む() if 宿mod else []
            if not 宿たち:
                print(f"::warning::{地['名']}の宿のリストが読めません。{日} {時}:00 は作りません。")
                continue
            # yu の3本をまとめて14日（前後）。地域のアカウントのその日（前後1日）の投稿に出る宿も外す
            地域の = _行たち(_取る(地["queue"], "posts/queue.jsonl"))
            避ける = (出ている宿(すでに + 足す, 宿mod, 宿たち, 日 - timedelta(days=14), 日 + timedelta(days=14))
                     | 出ている宿(地域の, 宿mod, 宿たち, 日 - timedelta(days=1), 日 + timedelta(days=1)))
            投稿 = 組み立てる(宿mod, 宿たち, 日, 時, 避ける, 地["名"])
            if not 投稿:
                print(f"::warning::{日} {時}:00（{地['名']}）の宿の投稿は作れませんでした。")
                continue
            足す.append(投稿)
            print(f"=== {時}:00 宿（{地['名']}）({len(投稿['text'])} 字) ===\n{投稿['text']}")
            for t in 投稿["thread"]:
                print(f"--- 返信 ---\n{t}")
    if os.environ.get("DRY_RUN", "").lower() == "true":
        print("DRY_RUN のため、キューには書き込みません。")
        return
    if 足す:
        with QUEUE.open("a", encoding="utf-8") as f:
            for e in 足す:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"キューに宿の投稿を {len(足す)} 本足しました。")


if __name__ == "__main__":
    main()
