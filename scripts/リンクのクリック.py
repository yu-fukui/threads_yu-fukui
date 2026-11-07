"""yu のアカウントで、リンクが押された回数を日ごとに取って insights/リンクのクリック.jsonl に残す。

2026-11-07 代表（統括経由）：楽天のリンクがアカウントごと・投稿ごとに何回押されたかを見たい。
転送ページをはさむのは楽天アフィリエイトのガイドライン（リンク先URLの変更・楽天以外の短縮URLの禁止）に
当たるおそれがあるのでやめ、Threads のインサイト API の clicks（リンクごとの回数）を読む。
福井・石川・ぎふあいちは scripts/アフィリの検証.py が同じものを非公開の置き場に残している。
個人の情報は取らない（リンクごとの回数だけ）。AI は使わない。

  python scripts/リンクのクリック.py        （THREADS_ACCESS_TOKEN が要る。LINK_DAYS で見る日数、既定 28）
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API = "https://graph.threads.net/v1.0"
JST = timezone(timedelta(hours=9))
記録 = Path("insights/リンクのクリック.jsonl")
見る日数 = int(os.environ.get("LINK_DAYS", "28"))


def get(path: str, **params) -> dict:
    params["access_token"] = os.environ["THREADS_ACCESS_TOKEN"]
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()[:300]}


def main() -> None:
    今日 = datetime.now(JST).date()
    me = get("me", fields="id")
    if "error" in me:
        raise SystemExit(f"アカウントを読めませんでした: {me['error']}")
    日ごと: dict[str, dict[str, int]] = {}
    for i in range(1, 見る日数 + 1):
        d = 今日 - timedelta(days=i)
        since = int(datetime(d.year, d.month, d.day, tzinfo=JST).timestamp())
        r = get(f"{me['id']}/threads_insights", metric="clicks", since=since, until=since + 86400)
        if "error" in r:
            print(f"{d} のクリックを取れませんでした: {r['error']}")
            continue
        日 = {}
        for item in r.get("data", []):
            for v in item.get("link_total_values") or item.get("values") or []:
                u = v.get("link_url")
                if u:
                    日[u] = 日.get(u, 0) + int(v.get("value", 0))
        日ごと[d.isoformat()] = 日
    記録.parent.mkdir(parents=True, exist_ok=True)
    with 記録.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"取った日": 今日.isoformat(), "日ごと": 日ごと}, ensure_ascii=False) + "\n")
    print(f"{len(日ごと)} 日ぶんのリンクのクリックを残しました（合計 {sum(sum(x.values()) for x in 日ごと.values())} 回）")


if __name__ == "__main__":
    main()
