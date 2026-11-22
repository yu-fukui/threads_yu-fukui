"""AI活用の毎日の投稿の「案」を作る（2026-11-23 代表「A：この案で始める・費用は yu の予算に入れる」、統括経由）

毎晩1回。公開リポジトリの最近の変更（コミットの題と説明）を材料に、
（2026-11-23 代表「まずYUで進めて」：B ができるまでは A 1本だけ。日によって B の題材＝やり方・失敗と直し方 も混ぜる）
  A … yu（このアカウント）1本：つくり手として感じたこと（2日後の 20:30）
  B … 新アカウント 2本：やり方・失敗と直し方（2日後の 12:10・21:10）
を Sonnet＋考える量 low で作り、機械の検査を通ったものだけを posts/AI活用の案.jsonl に足す。

**ここでは queue に入れない。** 始めの1〜2週間は、毎朝の作業（fukui-fukui/threads の scripts/判断待ち.py --yu）が
案をおでかけダッシュボードの判断待ちに出し、代表が「出す」を押したものだけが queue に入る。

書かないもの（材料からも先に外し、できた文も機械で止める）：
  金額・鍵や鍵に見える文字列・メールアドレス・URL・お客さま（主催者・読者）の名前や申込番号・
  有料案件や決済の中身・非公開の置き場の名前。
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import 使用量  # AI を呼ぶごとに使った量を残す（金額は書かない）

JST = ZoneInfo("Asia/Tokyo")
API = "https://api.anthropic.com/v1/messages"
案の置き場 = Path("posts/AI活用の案.jsonl")
使った材料 = Path("state/AI活用_使った材料.json")

# 材料にする公開リポジトリ。非公開のものは読めない（404）ので、自然に外れる
材料のリポジトリ = ["fukui-fukui/threads", "yu-fukui/threads_yu-fukui", "yu-fukui/ishikawa-odekake",
                 "yu-fukui/gifu-aichi-odekake"]
見る日数 = 7
材料の上限 = 15

# 2026-11-23 代表「まずYUで進めて」：新アカウント（B）ができるまでは yu（A）1本だけ作る（B の費用を足さない）。
# B を始めるときは、ワークフローの env に AI_B: "1" を足す
枠 = {"A": ["20:30"]}
if os.environ.get("AI_B") == "1":
    枠["B"] = ["12:10", "21:10"]

# ------------------------------------------------------------------
# 機械の検査（材料にも、できた文にも使う）
# ------------------------------------------------------------------
止める型 = [
    (r"[$＄]\s*\d|\d\s*(ドル|USD|円)|¥\s*\d|￥\s*\d", "金額"),
    (r"[A-Za-z0-9_\-]{28,}", "鍵に見える長い文字列"),
    (r"\b(sk-|ghp_|github_pat_|eyJ)[A-Za-z0-9_\-]{6,}", "鍵に見える文字列"),
    (r"[\w.+-]+@[\w-]+\.[\w.-]+", "メールアドレス"),
    (r"https?://|www\.", "URL"),
    (r"申込番号|client_reference|sub-\d|inq-\d|決済|Stripe|請求|仮押さえ|有料", "有料案件・決済"),
    (r"odekake-data|非公開の置き場|process_token|合言葉|パスワード|トークン|API ?キー|鍵", "非公開・鍵"),
    (r"(?<![仕同模多異王])様(?![々子])|主催者の|ご担当|お名前|読者の返信|返信の本文", "お客さまの情報"),
    (r"代表の(個人|家|住所|名前)", "代表の個人情報"),
]
煽り = ["必見", "知らないと損", "絶対", "神ツール", "神機能", "ヤバ", "やば", "最強", "爆速", "100倍", "激変", "革命", "保存版", "完全版"]
長さの上限 = 480


def 検査(文: str) -> list[str]:
    """止める理由の一覧（空なら通過）。"""
    ng = [名 for 型, 名 in 止める型 if re.search(型, 文)]
    ng += [f"煽り言葉「{w}」" for w in 煽り if w in 文]
    if len(文) > 長さの上限:
        ng.append(f"長すぎる（{len(文)}字）")
    if not 文.strip():
        ng.append("空")
    return ng


def 材料をきれいにする(文: str) -> str:
    """コミットの説明から、書いてはいけないものを含む行を落とす。"""
    出 = []
    for 行 in 文.splitlines():
        s = 行.strip()
        if not s or s.startswith(("Co-Authored-By", "Claude-Session", "Signed-off-by", "🤖", "http")):
            continue
        if any(re.search(型, s) for 型, _ in 止める型):
            continue
        出.append(s)
    return "\n".join(出)[:600]


# ------------------------------------------------------------------
# 材料を集める
# ------------------------------------------------------------------
def _get(url: str):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    if (t := os.environ.get("GITHUB_TOKEN")):
        req.add_header("Authorization", f"Bearer {t}")
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode())


def 材料を集める(今: datetime) -> list[dict]:
    try:
        済み = set(json.loads(使った材料.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        済み = set()
    since = (今 - timedelta(days=見る日数)).astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
    出 = []
    for r in 材料のリポジトリ:
        try:
            commits = _get(f"https://api.github.com/repos/{r}/commits?since={since}&per_page=100")
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            print(f"{r} は読めないので外します（{getattr(e, 'code', e)}）")
            continue
        for c in commits:
            sha = c.get("sha", "")
            msg = (c.get("commit") or {}).get("message", "")
            題 = msg.splitlines()[0] if msg else ""
            作者 = ((c.get("author") or {}).get("login") or "")
            # 毎日の自動の記録（chore）・マージ・ボットのコミットは材料にしない
            if not 題 or sha in 済み or 題.lower().startswith(("chore", "merge", "revert")) or 作者.endswith("[bot]"):
                continue
            本文 = 材料をきれいにする("\n".join(msg.splitlines()[1:]))
            題 = 材料をきれいにする(題)
            if not 題:
                continue
            日 = ((c.get("commit") or {}).get("committer") or {}).get("date", "")
            出.append({"sha": sha, "repo": r, "日": 日, "題": 題, "説明": 本文})
    出.sort(key=lambda x: x["日"], reverse=True)
    return 出[:材料の上限]


# ------------------------------------------------------------------
# AI に頼む
# ------------------------------------------------------------------
def yu_だけの頼み(日) -> str:
    """yu だけで回すときの1本。日によって、つくり手の目線と、やり方・失敗と直し方を交互にする（2026-11-23 代表「まずYUで」）。"""
    if 日.toordinal() % 2 == 0:
        return """■ A（1本）… 個人アカウント「yu」の投稿。つくり手として感じたこと。一人称は「わたし」。
  AI と一緒に作っていて気づいたこと・うまくいかなかったこと・ほっとしたことを、やわらかく。"""
    return """■ A（1本）… 個人アカウント「yu」の投稿。今日は「やり方・失敗と直し方」の回。一人称は「わたし」。
  「困りごと（何が起きたか）→ 原因 → どう直したか → 読む人がまねできる一言」の順で、やわらかい言葉で。"""


def 頼む文(材料: list[dict], 最近の案: list[str], 日=None) -> str:
    B = "B" in 枠
    並べ = "\n\n".join(f"[{i + 1}] {m['題']}\n{m['説明']}" for i, m in enumerate(材料))
    最近 = "\n---\n".join(最近の案[-12:]) or "（まだ無い）"
    return f"""あなたは、AI を使って地域のおでかけ情報サイトと Threads アカウントを運営している小さな会社の書き手です。
下の「材料」は、その会社の公開リポジトリで最近入った変更（コミットの題と説明）です。
これをもとに、Threads の投稿を{"3本" if B else "1本"}書いてください。

{頼みの本数(B, 日)}

■ 決まり（必ず守る）
- 材料に書いてある事実だけを書く。材料に無い数字・体験・成果・人数・期間を作らない。
- 金額・料金・費用の額、鍵・パスワード・URL・メールアドレス、お客さまや読者のこと、
  有料の申し込みや支払いのことは書かない。費用に触れるなら「約3分の1」のような割合だけ（材料にあるときだけ）。
- 煽り言葉（必見・知らないと損・絶対・最強・ヤバい・保存版 など）を使わない。
- ハッシュタグ・絵文字の連打・リンクは付けない。1本 400字以内。
- 専門用語（commit、workflow、env など）はそのまま使わず、ふつうの言葉に言いかえる。
- リポジトリ名・ファイル名・関数名は出さない。
- 最近の案と同じ話・同じ書き出しにしない。

■ 最近の案（重ねない）
{最近}

■ 材料
{並べ}

■ 出し方
JSON だけを出す（前後に説明を書かない）：
{出し方の例(B)}
"""


def 頼みの本数(B: bool, 日) -> str:
    if not B:
        return yu_だけの頼み(日 or datetime.now(JST).date())
    return """■ A（1本）… 個人アカウント「yu」の投稿。つくり手として感じたこと。一人称は「わたし」。
  AI と一緒に作っていて気づいたこと・うまくいかなかったこと・ほっとしたことを、やわらかく。
■ B（2本）… AI 活用の情報アカウントの投稿。やり方・失敗と直し方。
  「困りごと（何が起きたか）→ 原因 → どう直したか → 読む人がまねできる一言」の順で。
  2本は別の変更を材料にする。A とも別の切り口にする（同じ変更でも書き方を変える）。"""


def 出し方の例(B: bool) -> str:
    a = '{"A": [{"本文": "…", "材料": [番号]}]'
    if not B:
        return a + "}"
    return a + ', "B": [{"本文": "…", "材料": [番号]}, {"本文": "…", "材料": [番号]}]}'


def 聞く(prompt: str) -> str:
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    body = {"model": model, "max_tokens": int(os.environ.get("ANTHROPIC_MAX_TOKENS", "8000")),
            "messages": [{"role": "user", "content": prompt}]}
    # 考える量（Sonnet 5.5 は既定が high で、考える分だけで上限を使い切ることがある。2026-11-22 石川）
    if (e := os.environ.get("ANTHROPIC_EFFORT", "low").strip()):
        body["output_config"] = {"effort": e}
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method="POST")
    req.add_header("x-api-key", os.environ["ANTHROPIC_API_KEY"])
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("content-type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=240) as res:
            data = json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        print(f"::error::Anthropic API エラー ({e.code}): {e.read().decode(errors='replace')[:300]}")
        sys.exit(1)
    使用量.記録("AI活用の投稿", model, data.get("usage"))
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def JSONを取り出す(文: str) -> dict:
    m = re.search(r"\{.*\}", 文, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


# ------------------------------------------------------------------
def 案を読む() -> list[dict]:
    if not 案の置き場.exists():
        return []
    出 = []
    for l in 案の置き場.read_text(encoding="utf-8").splitlines():
        if l.strip() and not l.startswith("#"):
            try:
                出.append(json.loads(l))
            except json.JSONDecodeError:
                pass
    return 出


def main() -> None:
    今 = datetime.now(JST)
    # 2日先の分を作る：22:40 に作る → 翌朝 4:30 に判断待ちへ → 代表が答える → その次の朝 4:30 に queue へ → その日に出る
    日 = (今 + timedelta(days=2 if 今.hour >= 7 else 1)).date()
    if (t := os.environ.get("TARGET_DATE", "").strip()):
        日 = datetime.strptime(t, "%Y-%m-%d").date()
    既に = 案を読む()
    すでにある枠 = {x.get("id") for x in 既に}
    作る枠 = [(acc, hhmm) for acc, hs in 枠.items() for hhmm in hs
             if f"ai-{acc}-{日:%m%d}-{hhmm.replace(':', '')}" not in すでにある枠]
    if not 作る枠:
        print(f"{日} の案はもうあります")
        return
    材料 = 材料を集める(今)
    if not 材料:
        print("新しい材料が無いので作りません（AI は呼びません）")
        return
    print(f"材料 {len(材料)} 件（{', '.join(sorted({m['repo'] for m in 材料}))}）")
    答え = JSONを取り出す(聞く(頼む文(材料, [x.get("text", "") for x in 既に], 日)))
    if not 答え:
        print("::error::AI の答えを JSON として読めませんでした")
        sys.exit(1)
    新しい, 使った, 止めた = [], set(), 0
    for acc, hhmm in 作る枠:
        i = 枠[acc].index(hhmm)
        候補 = (答え.get(acc) or [])
        if i >= len(候補):
            continue
        文 = str(候補[i].get("本文") or "").strip()
        ng = 検査(文)
        if ng:
            止めた += 1
            print(f"::warning::{acc} {hhmm} の案は検査で止めました（{'・'.join(ng)}）")
            continue
        番号 = [n for n in 候補[i].get("材料") or [] if isinstance(n, int) and 1 <= n <= len(材料)]
        使った |= {材料[n - 1]["sha"] for n in 番号}
        新しい.append({
            "id": f"ai-{acc}-{日:%m%d}-{hhmm.replace(':', '')}",
            "アカウント": acc,
            "scheduled_at": f"{日.isoformat()}T{hhmm}:00+09:00",
            "text": 文,
            "材料": [材料[n - 1]["題"] for n in 番号],
            "作った時刻": 今.isoformat(timespec="seconds"),
        })
    if 新しい:
        案の置き場.parent.mkdir(parents=True, exist_ok=True)
        with 案の置き場.open("a", encoding="utf-8") as f:
            for x in 新しい:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
    if 使った:
        try:
            前 = json.loads(使った材料.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            前 = []
        使った材料.parent.mkdir(parents=True, exist_ok=True)
        使った材料.write_text(json.dumps((前 + sorted(使った))[-500:], ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{日} の案：{len(新しい)} 本を足しました（検査で止めたもの {止めた} 本）")


if __name__ == "__main__":
    main()
