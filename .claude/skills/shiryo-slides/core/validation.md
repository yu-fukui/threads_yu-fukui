# 視覚検証ループ

生成した HTML を Playwright で撮影 → AI が Vision で見て判定 → 直す、を繰り返す手順。
**「AI が自分で見て直す」がこのキットの中核**で、ここを省くと出来上がりの水準が落ちる。

`quick` / `full` は生成後に必ず実行（全枚 × 最大 2 周）。`edit` は編集スライド + 前後 1 枚に絞って最大 1 周。

## 1. Playwright のセットアップ確認（初回のみ）

ローカル `node_modules` とグローバル `npm root` の両方を探索してから判定する。

```bash
node -e "require('playwright')" 2>/dev/null \
  || NODE_PATH="$(npm root -g 2>/dev/null)" node -e "require('playwright')" 2>/dev/null \
  || echo "NEED_INSTALL"
```

何も出力されなければ OK。`NEED_INSTALL` が出た場合のみ、ユーザーに提示して承認を得る。

> 視覚検証に Playwright が必要です。以下を実行してよいですか？
> ```
> npm install -g playwright && npx playwright install chromium
> ```
> （初回のみ・約 400MB）

インストール後は同じワンライナーで再確認する。なお `scripts/capture.js` はグローバル `npm root -g` を `module.paths` に足す require ヘルパを内蔵しているので、グローバル導入済みなら `NODE_PATH` 無しで実行できる。上の判定だけが `node -e` を直接叩くためフォールバックを要する。

### 1-1. 未導入のまま進める場合

**生成のみを行い、視覚検証をスキップしてよい。** ただし黙って飛ばさない。

- **完了報告の冒頭に「視覚検証は未実施です」と必ず書く。** 続けて「Playwright が未導入のため、はみ出し・重なり・整列の自動確認を行っていません。ブラウザで開いて確認してください」と添える
- 末尾に埋もれさせない。理由は §2-1 のフォント問題と同じで、**受け取り手は劣化に気づけない**

## 2. キャプチャの実行

```bash
node "<スキルルート>/scripts/capture.js" "slides/<name>.html" "slides/.work/iter-0"
```

`<スキルルート>` は SKILL.md があるディレクトリの絶対パス。第 1 引数が入力 HTML、第 2 引数が出力先ディレクトリ（無ければ作成）。第 3 引数は任意で `--only=4,5,6` と書くと特定スライドだけを撮影する（1 始まり）。出力は `s01.png`, `s02.png`, …（ゼロ埋め 2 桁）で、枚数は `.s` 要素の数から自動検出する。

### 2-1. フォント警告が出たときの対応（必読）

`capture.js` には次の 2 点が入っている。

1. **Web フォントの読み込み完了を待ってから撮影する**（`document.fonts.ready` + `networkidle`）
2. **意図した書体で描画されていない場合に警告を出す**

判定は canvas の実測幅で行う。`document.fonts.check()` は該当の @font-face が存在しない場合も true を返す（フォールバックで描画できるとみなすため）ので、この用途には使えない。幅比較なら「CDN 経由でもローカル導入済みでも、意図した書体で描かれていれば OK」と判定できる。

撮影時にこう出たら止まる。

```
  警告: 以下の Web フォントが読み込めていません。
         - Noto Sans JP
  代替フォントで撮影されるため、意図した見た目と異なります。
  （社内プロキシで Google Fonts が塞がれている / オフラインの可能性）
```

**この警告が出ている間、スクショは見た目の判断に使えない。** 字幅も行高も別物なので、折り返し・はみ出し・詰まり具合の判定が実際と食い違う。ここで普通にループを回すと、代替フォントに合わせて文字サイズや改行を「直して」しまい、フォントが届く環境では逆に崩れる。

1. **切り分け** — `grep -n 'fonts.googleapis.com\|--ff' slides/<name>.html` で `<link>` と `--ff` / `--ff-en` を確認する。`<link>` が書けているのに落ちるならネットワーク側（プロキシ / オフライン）
2. **ローカル代替の確認** — `--ff` / `--ff-en` の後半にローカルフォントが並んでいるか。無ければ足す（テーマ定義の値が正）
3. **ネットワークが原因ならループは回さない。** レイアウト調整をせず、完了報告に明記する
   > Web フォント（Noto Sans JP）が取得できない環境のため、スクリーンショットは代替フォントで撮影されています。フォントが届く環境では見た目が変わります。文字の折り返しは未検証です。
4. **フォントが届く環境を用意できるなら、そちらで撮り直してからループを回す**

`フォント読み込み OK: ...` と出ていれば以降の判定は信用してよい。

### 2-2. DOM 幾何チェック（iter-0 で 1 回）

右下セーフエリアの侵食と、SVG の線・矢印がテキストを貫通していないかを、目視の前に洗い出す。

```bash
node - <<'NODE'
const { chromium } = require('playwright');
const file = 'slides/<name>.html';
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 960, height: 540 } });
  await p.goto('file://' + process.cwd() + '/' + file);
  const n = await p.locator('.s').count();
  for (let i = 0; i < n; i++) {
    const out = await p.evaluate((i) => {
      const all = document.querySelectorAll('.s'), res = [];
      all.forEach((el, j) => el.classList.toggle('active', j === i));
      document.elementsFromPoint(930, 520)
        .filter(e => !e.classList.contains('pn') && !e.classList.contains('s') && !['BODY', 'HTML'].includes(e.tagName))
        .forEach(e => res.push(`右下セーフエリアに ${e.tagName}.${String(e.className).split(' ')[0]}`));
      const pad = (r, n) => ({ x: r.x - n, y: r.y - n, w: r.width + n * 2, h: r.height + n * 2 });
      const hit = (a, b) => a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
      all[i].querySelectorAll('svg').forEach((svg, gi) => {
        const T = [...svg.querySelectorAll('text')].filter(e => !e.closest('defs'));
        [...svg.querySelectorAll('line,path')]
          .filter(e => !e.closest('defs') && (e.hasAttribute('stroke') || e.hasAttribute('marker-end')))
          .forEach(l => T.forEach(t => { if (hit(pad(l.getBBox(), 6), pad(t.getBBox(), 2)))
            res.push(`svg${gi + 1}: ${l.tagName} が text "${(t.textContent || '').trim().slice(0, 24)}" を貫通`); }));
      });
      return res;
    }, i);
    out.forEach(m => console.log(`slide ${i + 1}: ${m}`));
  }
  await b.close();
})();
NODE
```

完全自動判定ではなく候補の洗い出し。ヒットしたスライドは必ずスクショで目視する。

- 右下: 高さ数 px の単色ラインだけなら実害なし。テキスト付きの帯がヒットしたら、その帯に `padding-right: 80–100px` を入れて逃がす
- SVG: 説明テキストをノードの外側へ移す（中心線上・矢印経路上に置かない）／リーダー線を延ばす・曲げる・反対側から引く（12px 程度の短い線で文字を浮かせない）／ループ図は ENTRY・EXIT・補助ルールを本体から分離し内部には中心ラベルだけ残す
- 手描きの `<polygon>` 矢じりが見つかったら `<defs><marker orient="auto">` + `marker-end` に置換する

---

## 3. TODO ブロックは密度・余白チェックの対象外（除外規定）

材料が無い必須ブロックは TODO プレースホルダとして出力される（構成テンプレの TODO 仕様）。

**TODO ブロックを含むスライドは、密度チェックと余白チェックの対象から外す。**

- 対象外: 「content が薄い」「空白が過大」「情報量が足りない」「もう 1 要素足せる」系の判定すべて
- 対象内: はみ出し・重なり・整列・配色・禁止事項・フォントサイズ下限（＝TODO の中身を増やさずに直せるもの）

**なぜこの規定が要るか。** これが無いと「content が薄いなら content を増やす」という一般則が働き、**視覚検証ループ自体が TODO を埋める方向に圧力をかける**。埋める材料は無いので、AI は金額・体制・実績・スケジュールを創作する。その資料はそのまま客先に持ち込まれる。**嘘の数字を書かないことがこのキットの前提**であり、ここは配布物の安全要件として守る。

TODO スライドがスカスカに見えても、それが正しい出力である。埋めずに残し、完了報告で「N 枚が TODO です: 費用 / 体制 / 導入スケジュール」と列挙する。

## 4. Vision 判定の 3 観点

各 PNG を Read ツールで読み込み（Vision 対応）、次の 3 観点で洗い出す。

### 4-A. 機械的チェック

- **【最優先】下端 overflow** — **各 PNG の最下 20px を必ず見る**。`flex:1` のリストやモック内コンテンツが 540px を超えると最後の項目が切れる／押し出される。最後のリスト項目・カードが下端で切れていないか、ページ番号が要素に乗っていないか（最終行との間に 14px 以上の隙間があるか）。直し方は `padding-bottom` を 48–56px に増やす／内部の padding・gap・font を 1〜2 段階詰める／コンテンツを削る
- テキストが左右にはみ出していないか。ページ番号（右下の "N / N"）が出ているか
- **横並びカードの整列** — 各カードの番号上端・見出し上端・本文上端が水平に揃っているか（`core/rules.md` の `min-height` パターンで揃える）
- **奇妙な折り返し（1 文字落ち）** — 「卒 / 業」のように 1〜2 文字だけが次行に落ちていないか。各カードの最終行を逐一見る。直し方: 文言を 1〜2 字短縮／`<br>` で改行位置を明示／フォントを 1〜2px 縮める／箱を 10〜20px 広げる
- **過大な空白** — カード内の content 上下に 60px 以上の空きが無いか（TODO スライドは §3 により対象外）
- **ヘッダー帯の高さ統一** — 全スライドのヘッダー上端〜区切り線下端が揃っているか。1 枚でも h2 のサイズ・改行が違うとデッキ全体に響く
- **同一体裁の 3 連続** — 直前スライドと同じ体裁が 3 枚続いていないか。ヒットしたら**修正ではなく構成設計に戻る**（非テンプレ則）
- **片側カラーボーダーの混入** — 仕上げ後に必ず実行し、background を持つ要素のヒットのみ即修正（背景なしの罫線は対象外。`core/rules.md` §12 の 6 と同条件）
  ```bash
  perl -ne 'while(/<[a-z]+\b[^>]*>/g){ $t=$&;
    if($t=~/border-(left|right|top|bottom):\s*[0-9]+px solid var\(--accent/ && $t=~/background:\s*var\(/){
      print "$ARGV: カードに片側カラーボーダー: ", substr($t,0,90), "\n" } }' slides/*.html
  ```
- **マルチライン取り消し線** — `<br>` を含むテキストで 1 行目にしか線が入らないのは `::after` 方式のバグ。`text-decoration: line-through` に書き換える

### 4-B. AI 感チェック

`core/rules.md` の禁止事項と一致させる。

- グラデーション背景・`box-shadow`・光彩／絵文字や汎用アイコン（電球・歯車・ロケット）／自前で線描画した SVG アイコン
- `border-left` アクセントボックス／テーマの 16 変数の外の色（ネオン・蛍光・素の赤緑）
- `--accent` を文字色に使っていないか（文字は `--accent-deep`。テーマ定義の文字色規約が正）／角丸がテーマの `--radius` から外れていないか／整列が過剰で機械的に見えないか

### 4-C. コンテンツチェック

- 短文化が過剰で意味が削れていないか／図解 SVG が破綻していないか（線のズレ・要素の重なり・テキストが図形の外）
- ループ図・サイクル図で、読ませるラベルをノード間・矢印上・破線の境界内に置いていないか
- 文字サイズが小さすぎ／大きすぎないか。**基準値はテーマ定義（スケール 6 値）が正**
- 見出しの語法が用途テンプレに沿っているか（体言止めの統一、名詞の粒度）

### 4-D. 厳密レビューの心得

「ぱっと見問題なさそう」で済ませない。1 枚ずつ、次を確かめる。

1. 同種要素の y 位置を水平比較する。物差しで線を引くつもりで見る
2. 不格好な改行を探す（1〜2 文字落ち、句読点直後の改行）／最下 20px を見る
3. 空白の量を意識する（60px 以上の空き、列間の不揃い）／見出しが小さく感じないか、本文が読みにくくないか
4. **「これでいいか」と一度自問する。** Yes と即答できないなら直す

ユーザーから「全然ダメ」「整っていない」等の指摘を受けたら、サマリで済ませず全スライドを 1 枚ずつ Read で開き直す。

---

## 5. 面ルール検査（テーマ依存）

面の許容量だけはテーマごとに違う。**選択中のテーマ定義の「面ルール」（全面 / ブロックの 2 レベル）を読み、その値と突き合わせる。** 検査コードはテーマ非依存で、値だけをテーマから取る。

```bash
node - <<'NODE'
const { chromium } = require('playwright');
const file = 'slides/<name>.html';
const tokens = ['--ink-surface', '--accent'];   // 数えたい面の変数
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 960, height: 540 } });
  await p.goto('file://' + process.cwd() + '/' + file);
  const res = await p.evaluate((tokens) => {
    document.querySelectorAll('.s').forEach(el => el.classList.add('active'));
    const probe = document.body.appendChild(document.createElement('div'));
    const map = tokens.map(t => { probe.style.color = `var(${t})`; return [t, getComputedStyle(probe).color]; });
    probe.remove();
    const out = [];
    document.querySelectorAll('.s').forEach((s, i) => map.forEach(([t, c]) => {
      const els = [s, ...s.querySelectorAll('*')].filter(e => getComputedStyle(e).backgroundColor === c);
      const full = els.some(e => { const r = e.getBoundingClientRect(); return r.width * r.height > 960 * 540 * 0.8; });
      if (full) out.push(`slide ${i + 1}: ${t} 全面`);
      if (els.length - (full ? 1 : 0) > 0) out.push(`slide ${i + 1}: ${t} ブロック x${els.length - (full ? 1 : 0)}`);
    }));
    return out;
  }, tokens);
  res.forEach(r => console.log(r));
  await b.close();
})();
NODE
```

出力を集計し、テーマ定義の面ルールと照合する。「全面」行とは全面ダークの枚数・連続の可否を、「ブロック」行とは 1 スライドあたりの個数・デッキ全体の枚数・連続枚数を、「アクセント面」行とは `--accent` 塗りが 1 スライドに 2 箇所以上ないかを突き合わせる。

超過していたら、**色を薄めるのではなく面を減らす。** 落とす候補は「結論でないスライド」から。並列カードの一部だけを塗っているものが最初に落ちる。強調したいスライドが余るときは、地を `--surface`、カードを `--bg` に反転する強調面（テーマ定義の該当節）へ振り替える。

---

## 6. 全枚チェックは必須・サンプリング禁止

**全枚（s01〜sNN）を例外なく 1 枚ずつ Read で開く。** 「自分が変えたスライドだけ見れば十分」は罠。CSS 変数・共通クラス・padding / flex / font の変更は、変えていないスライドにも波及する。

- `.pn` の位置変更 → 全スライドで下端要素と衝突しうる／共通 padding の変更 → `flex:1` が再計算され下端がはみ出す
- `font-size` の全体調整 → 全枚で改行位置が変わり、1 文字落ちが新規に発生する

サンプリングしてよいケースは無い。例外は `edit` モード（編集スライド + 前後 1 枚）だけ。`Write` で全置換した後はとくに、途中で「ここは変えていないから飛ばしていい」と判断しない。**判断する前に開く。**

## 7. ループ本体

```
1. capture.js を実行      → slides/.work/iter-0/ に s01.png〜sNN.png
2. フォント警告を確認      → 出ていたら §2-1 へ（ループは回さない）
3. §2-2 の DOM 幾何チェックと §5 の面ルール検査を実行
4. 全 PNG を Read で読み、§4 の 3 観点で問題を洗い出す
   （TODO ブロックを含むスライドは密度・余白の判定から外す。§3）
5. 修正対象が無ければ完了（早期終了）
6. 該当スライドの HTML を Edit で修正
7. capture.js 再実行      → slides/.work/iter-1/
8. 4〜7 を繰り返す。上限:
     quick / full : 2 周（iter-0 → iter-1 → iter-2）
     edit         : 1 周（iter-0 → iter-1）
9. 上限到達後も残る問題はユーザーに報告する
     "以下は iter-2 でも残っています:
       - s03.png: 見出しが枠からはみ出している
       - s07.png: 3 列カードの本文上端が揃っていない
      手動で確認・修正してください。"
```

### 7-1. edit モードの部分検証

```bash
# 5 枚目を編集した場合 → 4, 5, 6 を撮影
node "<スキルルート>/scripts/capture.js" "slides/<name>.html" "slides/.work/iter-0" --only=4,5,6
```

観点は §4 と同じ。加えて、前後スライドとの体裁連続性（同一パターン 3 連続になっていないか）と、ページ番号の分母を見る。枚数が変わったなら全スライドの更新が要る＝全枚撮り直しに切り替える。自動修正は 1 周まで。それ以上はユーザー確認に回す。

## 8. ループ後

`.work/iter-*/` は残す（履歴確認用。削除はユーザー判断、`.gitignore` 推奨）。完了報告には次を含める。

1. **視覚検証を実施したかどうか**（未実施なら冒頭に明示。§1-1）／フォント警告の有無（出ていたなら §2-1 の文面）
2. 自動修正した箇所の要約／TODO スライドの一覧／上限到達後も残った問題（あれば）
