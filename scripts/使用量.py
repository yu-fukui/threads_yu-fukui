"""AI（Anthropic API）を1回呼ぶごとに、使った量を state/usage.jsonl に1行ずつ残す。

2026-10-19 代表「おすすめの設定で進めて」（統括経由）：yu の使用量もおでかけダッシュボードの費用タブに出す。
このリポジトリは公開なので、**金額は書かない**（トークン数・検索回数・モデルだけ）。
金額は、非公開の置き場で費用ダッシュボード（fukui-fukui/threads の scripts/費用ダッシュボード.py）が計算する。
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

置き場 = Path("state/usage.jsonl")


def 起動() -> str:
    """定期（cron-job.org の repository_dispatch と GitHub の schedule）か、手動・追加か。"""
    return "定期" if os.environ.get("GITHUB_EVENT_NAME") in ("repository_dispatch", "schedule") else "手動"


def 記録(何: str, モデル: str, usage: dict | None, 検索: int | None = None) -> None:
    """1行足す。記録に失敗しても本来の仕事は止めない。"""
    try:
        u = usage or {}
        if 検索 is None:
            検索 = int((u.get("server_tool_use") or {}).get("web_search_requests") or 0)
        行 = {
            "時刻": datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
            "何": 何,
            "モデル": モデル,
            "入力": (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0),
            "出力": u.get("output_tokens") or 0,
            "検索": 検索,
            "起動": 起動(),
        }
        置き場.parent.mkdir(parents=True, exist_ok=True)
        with 置き場.open("a", encoding="utf-8") as f:
            f.write(json.dumps(行, ensure_ascii=False) + "\n")
    except Exception as exc:  # noqa: BLE001
        print(f"::warning::使用量を記録できませんでした（{exc}）")
