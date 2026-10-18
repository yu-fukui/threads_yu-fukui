# レイアウト規範 & 実装仕様

全テーマ共通のコア。**このファイルの値・規則はテーマに依存しない。**
色・書体・角丸・面の許容量・見出しサイズはテーマ定義（`themes/theme-<x>.md`）が正本で、
このファイルにサイズの実数を直書きしない。

---

## 1. 絶対禁止事項

以下は**いかなる場合も使用禁止**。1 つでも含まれていれば不合格。

| # | 禁止項目 | 理由 |
|---|---|---|
| 1 | カードの色付き片側ボーダー（`border-left` / `border-top` / `border-right` / `border-bottom`） | 縁に色付きボーダーを入れたカードは典型的な「AI が作った感じ」。色分けが必要なら (a) 大きいナンバーバッジに色を付ける (b) カード見出しの文字色を変える (c) 小さなドット（10px 丸） (d) 全周ボーダー（4 辺すべて）のいずれかで表現する。**例外**: 表組みの列区切り `border-left:1px solid var(--line)` は可。background を持たない要素への単色の罫線（見出し上の `border-top` 等）は罫線であり対象外 |
| 2 | 絵文字 | ブランドトーンに合わない。装飾は SVG / CSS で行う |
| 3 | ナビゲーションヒントテキスト（「←→で操作」等） | 操作は直感的に行える。表示は不要 |
| 4 | 外部画像 `<img>` タグ | 図解はすべてインライン SVG で作る。単一 HTML 完結が原則 |
| 5 | `box-shadow` / `text-shadow` | フラットなデザインを維持する |
| 6 | `linear-gradient` / `radial-gradient` | グラデーション背景は AI 感の元 |
| 7 | `transition` / `animation` / `@keyframes` | スライドにアニメーションは不要 |
| 8 | `--radius` を超える角丸の直書き | 角丸はテーマ定義の 1 値に統一する。**例外**: 正円バッジ（直径 44px 以下の `border-radius:50%`） |
| 9 | ネオン色・蛍光色 | テーマのトークン以外のアクセント色は使わない |
| 10 | 外部 CSS / 外部 JS ファイル | 単一 HTML 完結。**唯一の例外は Google Fonts の `<link>`**（テーマ定義参照） |
| 11 | `::after` 絶対配置の取り消し線 | 複数行テキストで 1 行目にしか線が入らないバグの温床。`text-decoration:line-through` + `text-decoration-thickness` を使う |
| 12 | ループ図・サイクル図で**矢印の経路上**にテキストラベルを置く | 矢印（line/path）と text の bounding box が重なり、必ず「矢印が文字を貫通している」と指摘される。説明テキストはノードの**外側**（中心軸の反対側）に置く |
| 13 | SVG の `<path d="M... A..."/>`（arc）+ 手動 `<polygon>` の矢じり | arc の接線方向と手動 polygon の向きが一致せず、必ず矢じりが浮く／逆を向く。**矢じりは必ず `<defs><marker>` + `marker-end`**（§8） |
| 14 | SVG で `<text x="X">語1</text><text x="X+W">語2</text>` のように**ハードコード x で語を並べる** | 単語間隔が崩れて不自然な空白が空く。1 つの `<text>` 内で `<tspan>` を使うか HTML で組む |
| 15 | 縦書き（`transform="rotate(-90 ...)"`）でラベルを読ませる | 視認性が極端に落ちる。横並びチップに置き換える |
| 16 | 円形 dashed boundary（`<circle stroke-dasharray>` の装飾枠）の内側にラベルを置く | 視覚ノイズが強くラベルと干渉する。境界が意味を持つなら実線＋ラベル、装飾目的なら削除 |
| 17 | 見出し（h1 / h2 / 焦点コピー）の**末尾に句点（。）** | 見出しは文末を意図しない。「Git は戻せる。GitHub は届く。」のようなコピー型でも不要。中間に区切りが要るなら `<br>` で改行する |
| 18 | 見出しに**飾りの読点（、）** | 見出しは短く言い切る。語調を整えるためだけの読点は削る（「毎回、ゼロから」→「毎回ゼロから」）。`<br>` 直前の読点は改行がポーズを担うので必ず削る。**残してよいのは並列・対比を示す構造的な区切りだけ**（「どこまで人、どこからAI」）。本文・話し言葉の引用は対象外 |
| 19 | 自前の SVG で**矢印 / タイムライン / 接続線**を多用する | 「矢印が中途半端」「ズレている」と必ず指摘される。線描画 SVG は最小化し、HTML ピル＋テキスト矢印で代用する（§9） |
| 20 | アイコンを自前で SVG 線描画する | 雲・人・ファイル・チェック等の単一シンボルを手描き SVG で再現すると必ず「何のアイコンか分からない」と指摘される。ライブラリから取得してインライン貼り付けする（§10） |
| 21 | 字間の広いラベル（`letter-spacing` が `.1em` 以上）に**固有名詞**を入れる | 「G I T H U B」のように表示されブランド表記として違和感が出る。固有名詞は `letter-spacing:.02em` 以下の専用スタイルで書く |
| 22 | 並列カード（同じ役割で列挙されたカード行・グリッド）の**中の 1〜2 枚だけ**背景色・文字色を変える | 「揃っていない」「色を変える意味が分からない」と必ず指摘される。**「最終ステップの強調」「重要要素のハイライト」目的でも禁止**。並列セットは背景・文字色とも完全に統一する。**例外**: 左右 2 枚の対比構図（Before/After・NG/OK）でライト面×ダーク面を使い分けるのは対比の意味があるので可 |
| 23 | 進行予告テキスト（「このあと〜を見る」「次から〜」「Step 1〜6 で順番に」） | スライドは 1 枚で完結させる。進行の説明は話し手がやる |

---

## 2. AI 感排除チェック

生成後、以下を自己チェックする。

- [ ] グラデーション背景を使っていないか
- [ ] 過剰な装飾（影・光彩・反射）がないか
- [ ] 汎用的すぎるアイコン（電球・歯車・ロケット）を使っていないか
- [ ] カードに色付き片側ボーダーが混入していないか（§1 #1）
- [ ] すべての色が `var()` 経由か（ハードコード禁止。`#fff` のみ例外）
- [ ] 同じ体裁のスライドが 3 枚以上続いていないか（§3）

---

## 3. テンプレ化の症状 — card grid 連発

**3〜4 列の等幅カードが 3 枚連続したら、そのスライドを直すのではなく構成設計に戻る。**

これはテンプレ化の最大の症状。内容が違うのに見た目が同じということは、内容固有の構造を捨てて器に流し込んでいる。

判定:

- 3 枚連続 → 要再設計
- デッキ全体の 30% 超が card grid → 要再設計

対処は「カードの色を変える」ではなく、**内容の性質に合ったレイアウトを選び直す**こと（`core/structure.md` のメタファー集を参照）。

---

## 4. 整列の絶対ルール

複数カードを横並びにするとき、**カード間で同じ役割の要素は必ず同じ y 位置に揃える**。ナンバー・見出し・本文の開始位置がカードごとにズレているスライドは即不合格。

### 4-1. よくある失敗

```html
<!-- NG: 見出しの行数が違うと本文の開始位置がズレる -->
<div style="display:flex;gap:20px">
  <div><h3>短い見出し</h3><p>本文</p></div>
  <div><h3>とても長い見出しで2行になる</h3><p>本文</p></div>
</div>
```

### 4-2. 正しい書き方

```html
<!-- OK: 見出しに min-height を与えて開始位置を揃える -->
<div style="display:flex;gap:20px;align-items:stretch">
  <div style="flex:1;display:flex;flex-direction:column">
    <h3 style="min-height:2.6em">短い見出し</h3>
    <p>本文</p>
  </div>
  <div style="flex:1;display:flex;flex-direction:column">
    <h3 style="min-height:2.6em">とても長い見出しで2行になる</h3>
    <p>本文</p>
  </div>
</div>
```

### 4-3. カード幅の決め方

- カードが「等しい重さの並列要素」なら `flex:1` で**等幅**にする
- **比率に意味がある**場合（第1-3回=25% / 第4-8回=42% / 第9-12回=33%）だけ幅を変える。幅とラベルで同じ情報を二重に符号化しない
- 横並びカードの**下端は必ず揃える**（`align-items:stretch`）

---

## 5. 余白とフォント密度

### 5-1. サイズの正本

**h1 / h2 / 本文 / KI ラベルの基準サイズはテーマ定義が正本。** このファイルでは実数を定めない。テーマ定義の 6 値を参照すること。

テーマが規定しないサイズ（カード見出し・番号・注釈・SVG 内ラベル）は以下を守る:

| 用途 | 下限 |
|---|---|
| 読ませる本文・カード内テキスト | テーマの本文サイズ − 2px まで |
| 注記（※）・図中のラベル（バー内の文字・軸ラベル・補足の 1 行） | 12px |
| SVG 内の意味を持つラベル | 13px |
| 装飾ラベル（ページ番号・KI・略号） | 制限なし（読ませないため） |

**「本文」と「図中のラベル」を区別する。** 本文は段落として読ませる文章、図中のラベルは図を見るときに目が拾う短い語。後者に本文サイズを要求すると図が破綻する。逆に、段落を 12px に落として情報を詰め込むのは禁止。

### 5-2. 縦の「間延び」を作らない

`justify-content:space-between` で要素を上下に引き離すと、中央に意味のない空白ができる。**要素は上から自然に積み、余りは下に残す。**

```css
/* NG */ .zone{height:100%;display:flex;flex-direction:column;justify-content:space-between}
/* OK */ .zone{height:100%;display:flex;flex-direction:column;gap:18px}
```

### 5-3. 文字の折り返し確認

h2 と本文は**必ず 2 行以内**に収まるか確認する。3 行になったら**フォントを下げるのではなく文言を短くする**。

---

## 6. ヘッダーの統一

デッキ全体で以下を完全に統一する。1 枚でも違うと「雑」に見える。

- h2 のサイズ（テーマ規定値。2 行化時のみテーマが許す縮小値）
- 見出しラベル（KI）のマージン
- 左右パディング
- 見出し下の区切り罫の有無と太さ

**中面の基本構造**: KI ラベル → h2 → 区切り罫 → 本体。

---

## 7. ページ番号と下端要素

### 7-1. 仕様

- 位置: 右下（`bottom:18px; right:22px`）
- 書式: `N / 総数`
- 色: `var(--dim)`。ダーク面では `var(--on-dark)` を透過 60% で
- **表紙にも入れる**（連番の欠落は事故に見える）

### 7-2. 右下セーフエリアの予約

**右下 120 × 40px にはコンテンツを置かない。** 下端に全幅バーやテキストを置く場合は `margin-right:100px` を確保する。

---

## 8. SVG 矢印の標準実装

**矢じりは必ず `<defs><marker>` + `marker-end` で描く。** 手動 `<polygon>` は禁止（§1 #13）。

```html
<svg viewBox="0 0 400 100" style="width:100%;height:auto">
  <defs>
    <marker id="ah" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--accent)"/>
    </marker>
  </defs>
  <line x1="20" y1="50" x2="380" y2="50"
        stroke="var(--accent)" stroke-width="2" marker-end="url(#ah)"/>
</svg>
```

ルール:

- `id` はスライドごとに一意にする（`ah-s03` など）。重複すると後勝ちで別の色になる
- `orient="auto-start-reverse"` を付ける（始点側にも矢じりを付けられる）
- 矢じりの色は線と同じ `var()` を使う
- **矢印の経路上にテキストを置かない**（§1 #12）

---

## 9. 線描画 SVG の最小化

**複雑なグラフ（分岐・合流、スイムレーン）以外は線 SVG を使わない。** HTML のピル＋テキスト矢印で代用する。

```html
<div style="display:flex;align-items:center;gap:14px">
  <span style="background:var(--accent-tint);color:var(--ink);
               padding:10px 18px;border-radius:var(--radius);font-weight:700">受付</span>
  <span style="color:var(--accent-deep);font-size:20px">→</span>
  <span style="background:var(--accent-tint);color:var(--ink);
               padding:10px 18px;border-radius:var(--radius);font-weight:700">一次回答</span>
  <span style="color:var(--accent-deep);font-size:20px">→</span>
  <span style="background:var(--accent-tint);color:var(--ink);
               padding:10px 18px;border-radius:var(--radius);font-weight:700">担当者</span>
</div>
```

使える矢印記号: `→ ← ↑ ↓ ↔ ⇄ ─`

**SVG 1 個に line + polygon が 4 個以上あったら HTML 化を検討する。**

---

## 10. アイコン運用

### 10-1. 自前で描かない

雲・人・ファイル・チェック・地球儀などの単一シンボルを手描き SVG で再現しようとすると、必ず「何のアイコンか分からない」と指摘される。**ライブラリから取得してインラインで貼る。**

### 10-2. 使うライブラリ

**Lucide**（https://lucide.dev）を既定とする。MIT ライセンスで商用利用可。1 本の統一されたストロークで、線の太さがスライドの罫線と馴染む。

補助的に **Heroicons**（MIT）、Git 関連は **Octicons**（MIT）。**3 つを 1 枚のスライドで混ぜない。**

### 10-3. 取得と貼り方

`https://lucide.dev/icons/<name>` を WebFetch して SVG を取り出すか、既知の形状を手で書く場合も**必ず `stroke="currentColor"` `fill="none"` の形に整える**。

```html
<!-- Lucide の SVG をインライン化する際の必須の整形 -->
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"
     viewBox="0 0 24 24" fill="none" stroke="currentColor"
     stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
     style="color:var(--accent-deep)">
  <!-- path はライブラリからそのまま -->
</svg>
```

ルール:

- `stroke="currentColor"` にして、色は親要素の `color` で指定する（テーマトークンを使うため）
- `width` / `height` は用途別サイズ（§10-4）に合わせて上書きする
- ライブラリ既定の `stroke-width:2` を変えない（変えると別のアイコンと不揃いになる）
- `<title>` は入れない（読み上げ不要・スライドは視覚メディア）

### 10-4. サイズの目安

| 用途 | サイズ |
|---|---|
| 本文行内 | 16px |
| カード見出しの左 | 20px |
| 図解のノード内 | 28〜32px |
| 単独で意味を担う主役 | 40〜48px |

### 10-5. 使わなくてよい

**アイコンは「無いと意味が伝わらない」ときだけ使う。** 見出しの左に飾りで付けるのは AI 感の典型。迷ったら付けない。

---

## 11. 実装テンプレート（必須）

960×540 の設計キャンバスで作り、ビューポートに合わせて拡大縮小する。
`<body>` 直後のマーカーは **edit モードがテーマ・用途・スタイルを判定するために使う**ので必ず入れる。
旧形式（`v1.0`・style なし）は `style:standard viz:mid` として扱う（後方互換）。

```html
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title><デッキタイトル></title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="<テーマ定義の Google Fonts URL>" rel="stylesheet">
<style>
  :root{ /* テーマ定義の 16 変数をここに展開 */ }
  html,body{margin:0;padding:0;background:var(--bg);overflow:hidden}
  .s{
    position:absolute;top:50%;left:50%;width:960px;height:540px;
    transform:translate(-50%,-50%) scale(var(--k,1));transform-origin:center center;
    background:var(--bg);color:var(--ink);font-family:var(--ff);
    visibility:hidden;opacity:0;display:flex;flex-direction:column;
  }
  .s.active{visibility:visible;opacity:1}
  /* 以降、共通コンポーネント */
</style>
</head>
<body>
<!-- kit:slide-zukai-kit v1.1 theme:B use:proposal style:formal viz:low -->

<div class="s active"> ... </div>
<div class="s"> ... </div>

<script>
function fit(){document.documentElement.style.setProperty('--k',Math.min(innerWidth/960,innerHeight/540))}
addEventListener('resize',fit);fit();
let i=0;const slides=document.querySelectorAll('.s');
function show(n){i=Math.max(0,Math.min(slides.length-1,n));slides.forEach((el,j)=>el.classList.toggle('active',j===i))}
addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key===' ')show(i+1);if(e.key==='ArrowLeft')show(i-1)});
show(0);
</script>
</body>
</html>
```

- **`.s` を `display:none` で隠さない**（`visibility` + `opacity` を使う）。PDF 化のとき、フォントのサブセットが 1 枚目分しか読み込まれず、他のスライドの文字だけ別フォントに落ちる
- 操作の説明テキストは画面に出さない（§1 #3）

---

## 12. iter-0 preflight（撮影前に必ず全件実行）

過去に繰り返し指摘された問題を、Playwright で撮影する前に機械検出する。**ヒットを放置して撮影に進まない。**

> **検査を書き足すときの注意（日本語特有の罠）**
> Perl は `use utf8` を付けないと、正規表現の**文字クラス `[...]` の中の日本語文字をバイト単位で扱う**。
> `/[、。]/` と書くと 6 バイトの集合になり、**日本語テキストのほぼ全てに誤爆する**。
> 日本語文字は `/、/` のように**文字クラスの外に単独で書く**か、`perl -CSD -Mutf8` を付ける。

```bash
# 1. 読ませるテキストの極小化（装飾ラベル以外は拡大する）
grep -nE 'font-size="(9|10|11|12)"|font-size:(9|10|10\.5|11|12|12\.5)px' slides/*.html

# 2. SVG 内の主要ラベルが小さすぎる（13px 以上へ）
grep -nE '<text[^>]*font-size="(9|10|11|12)"' slides/*.html

# 3. 表紙 h1 の 3 行化（<br> が 2 個以上なら原則修正）
perl -0ne 'while(/<div class="s active"[\s\S]*?<h1\b[^>]*>([\s\S]*?)<\/h1>/g){$n=()=$1=~/<br\s*\/?>/g; print "$ARGV: 表紙 h1 に br が $n 個\n" if $n>=2}' slides/*.html

# 4. h2 が長すぎる（35 文字超は 2 行化または短縮。フォントは下げない）
grep -nE '<h2[^>]*>([^<]|<span[^>]*>[^<]*</span>){35,}' slides/*.html

# 5. 下端の全幅バー（ページ番号と干渉する候補）
grep -nE 'position:absolute;bottom:0;left:0;right:0' slides/*.html

# 6. カードの片側カラーボーダー禁止（§1 #1）
#    同一タグ内に background があるもの（＝カード）だけを検出する。
#    background を持たない要素の色付き border は「罫線・下線」なので対象外
perl -ne 'while(/<[a-z]+\b[^>]*>/g){ $t=$&;
  if($t=~/border-(left|right|top|bottom):\s*[0-9]+px solid var\(--accent/ && $t=~/background:\s*var\(/){
    print "$ARGV: カードに片側カラーボーダー: ", substr($t,0,90), "\n" } }' slides/*.html

# 6-B. 文字を載せた --accent 塗り（テーマ規約違反）
#      --accent は明度が高く、白文字ではコントラスト不足、黒文字では視覚的に重い。
#      文字を載せる塗りは --accent-deep + 白文字にする（テーマ定義の文字色規約）
perl -ne 'while(/<[a-z]+\b[^>]*>/g){ $t=$&;
  if($t=~/background:\s*var\(--accent\)/ && $t=~/(color:|font-size:|font-weight:)/){
    print "$ARGV: --accent 塗りに文字が載っている → --accent-deep + 白文字へ: ", substr($t,0,90), "\n" } }' slides/*.html

# 7. ハードコード色禁止（#fff のみ例外）
grep -nE 'background:\s*#[0-9a-fA-F]{3,8};|color:\s*#[0-9a-fA-F]{3,8};|fill="#[0-9a-fA-F]{3,8}"|stroke="#[0-9a-fA-F]{3,8}"' slides/*.html | grep -v '#fff'

# 8. AI 感の強い装飾（§1 #5 #6 #7）
grep -nE 'box-shadow|text-shadow|linear-gradient|radial-gradient|animation|transition:|@keyframes' slides/*.html

# 9. SVG の手動 polygon 矢じり（§1 #13）
grep -nE '<polygon[^>]*(points|fill=)' slides/*.html

# 10. SVG の回転テキスト・縦書き（§1 #15）
grep -nE '<text[^>]*transform="rotate\(|writing-mode|text-orientation' slides/*.html

# 11. SVG で単語ごとに text x をハードコード（§1 #14）
perl -0ne 'while(/<svg\b[\s\S]*?<\/svg>/g){$svg=$&; if($svg =~ /<text\b[^>]*\bx="[^"]+"[\s\S]{0,120}<text\b[^>]*\bx="[^"]+"[\s\S]{0,120}<text\b[^>]*\bx="[^"]+"/){print "$ARGV: SVG text x のハードコード連続\n"}}' slides/*.html

# 12. SVG の line/path と text の重なり候補（DOM 幾何チェックで確認する）
perl -0ne 'while(/<svg\b[\s\S]*?<\/svg>/g){$svg=$&; if($svg =~ /<(line|path)\b/ && $svg =~ /<text\b[^>]*\by="[^"]+"/){print "$ARGV: SVG line/path + text の重なり候補\n"}}' slides/*.html

# 13. SVG text 同士の y が近い（ラベル衝突候補）
perl -0ne 'while(/<svg\b[\s\S]*?<\/svg>/g){$svg=$&; @ys=($svg =~ /<text\b[^>]*\by="([0-9.]+)"/g); for($i=0;$i<@ys;$i++){for($j=$i+1;$j<@ys;$j++){if(abs($ys[$i]-$ys[$j])<14){print "$ARGV: SVG text の y が近接 $ys[$i] / $ys[$j]\n"; last}}}}' slides/*.html

# 14. card grid 連発（§3）
perl -0ne 'while(/<div class="s\b[\s\S]*?(?=<div class="s\b|<\/body>)/g){$i++; $b=$&; print "スライド $i: card grid 候補\n" if $b =~ /grid-template-columns:repeat\([3-5],1fr\)/}' slides/*.html

# 15-16. 見出しの句点・飾り読点（§1 #17 #18）
#   見出しの中身からタグを除去してから判定する。
#   単純な grep だと <br> や <span> を跨いだ句読点を取りこぼす
perl -0ne 'while(/<h([12])\b[^>]*>([\s\S]*?)<\/h\1>/g){ $t=$2; $t=~s/<[^>]*>//g;
  print "$ARGV: 見出しに読点 → $t\n" if $t=~/、/;
  print "$ARGV: 見出しに句点 → $t\n" if $t=~/。/ }' slides/*.html
# 読点は原則削除。並列・対比の構造区切り（「どこまで人、どこからAI」）だけ残す

# 17. 線描画 SVG の過剰使用（§9）
perl -0ne 'while(/<svg\b[\s\S]*?<\/svg>/g){$svg=$&; $l=()=$svg=~/<line\b/g; $p=()=$svg=~/<polygon\b/g; print "$ARGV: SVG に line $l + polygon $p（HTML 化を検討）\n" if $l+$p>=4}' slides/*.html

# 18. 並列カード内で一部だけ色が違う候補（§1 #22）
perl -0ne 'while(/<div class="s\b[\s\S]*?(?=<div class="s\b|<\/body>)/g){$i++; $b=$&; if($b =~ /background:var\(--accent-tint\)/ && $b =~ /background:var\(--surface\)/ && $b =~ /display:flex/){print "スライド $i: 並列カードの色混在候補\n"}}' slides/*.html

# 19. 進行予告テキスト（§1 #23）
grep -nE 'このあと|次から|後ほど|お見せします|順番に見て' slides/*.html

# 20. フォントのローカル代替が書かれているか（ヒット 0 件なら違反）
grep -cE '\-\-ff:[^;]*(Hiragino|Yu Gothic|Meiryo|sans-serif)' slides/*.html

# 21. 直前スライドと同じ体裁の反復（3 枚連続で同じ構造なら要再設計）
perl -0ne '@s=/<div class="s\b[\s\S]*?(?=<div class="s\b|<\/body>)/g; for $i (2..$#s){ $sig=sub{my $x=shift; join(",", $x=~/(grid-template-columns:[^;"]+|display:flex)/g)}; if($sig->($s[$i]) ne "" && $sig->($s[$i]) eq $sig->($s[$i-1]) && $sig->($s[$i]) eq $sig->($s[$i-2])){print "スライド ".($i+1).": 直前2枚と同じ体裁\n"} }' slides/*.html
```

### 12-1. 面ルール検査（テーマ依存）

**テーマ定義の面ルールから許容値を読んで検査する。** 許容値はテーマごとに違うため、この項目だけテーマ非依存にならない。

```bash
# 全面ダークのスライド枚数を数える（トップレベル .s のみ）
perl -0ne '$n=0; while(/<div class="s\b[^>]*style="[^"]*background:var\(--ink-surface\)/g){$n++} print "全面ダーク: $n 枚\n"' slides/*.html

# ダークブロックの総数
grep -o 'background:var(--ink-surface)' slides/*.html | wc -l
```

テーマ定義の「全面 N 枚まで / ブロック M 枚まで」と突き合わせ、超過していたら修正する。

**判定注記**: スカイライン型（`core/structure.md` §8-N）の**沈みブロック**は図のデータの一部なので、ダークブロックの集計から除外する。上の grep は数え分けられないため手で差し引き、例外として完了報告に記す。ただしスカイラインを置いた枚に**それ以外の**ダークブロックがあれば、通常どおり超過として扱う。

### 12-2. 判定の指針

| 項目 | 対応 |
|---|---|
| 1, 2（極小フォント） | 装飾ラベル・注記・図中のラベルはヒットしてよい（§5-1 の下限表で判定）。**段落として読ませる本文**だけ拡大する |
| 3（表紙 h1 3 行） | 即修正。修飾語をサブテキストに逃がす |
| 4（h2 長すぎ） | 短縮するか `<br>` で 2 行化。**フォントは下げない** |
| 6〜10（既存禁止事項） | 即修正 |
| 9（polygon） | 矢じり以外の polygon なら例外可。矢印なら `marker-end` へ置換 |
| 11 | 3 つ以上の語を別 text で並べていたら `<tspan>` か HTML へ |
| 12, 13 | 候補が出たら DOM 幾何チェック（`core/validation.md`）で確認 |
| 14, 21 | 3 枚連続なら**構成設計に戻る**（§3）。TODO ブロック同士のスライドは同一体裁 3 連続に数えない（体裁固定は TODO 仕様の一部） |
| 15 | 句点は即削除 |
| 16 | 読点は原則削除。並列・対比の構造区切りだけ残す |
| 18 | 左右 2 枚の対比構図なら可。並列セット内の単独色変えは統一する |
| 20 | **0 件ならローカル代替が抜けている。必ず追加する** |

### 12-3. iter-0 完了の定義

- 1〜21 と面ルール検査を**全件実行した**
- ヒットは修正済みか、例外として残す理由を完了報告に書ける
- 全スライドを 1 枚ずつ目視して違和感がない

「ぱっと見良さそう」で撮影に進まない。

---

## 13. 完了前セルフチェック

- [ ] card grid が 3 枚連続していないか（§3）
- [ ] 並列カード・チップの中で 1 枚だけ色が違う箇所がないか（§1 #22）
- [ ] テキスト列挙で説明しているスライドを、図解に置き換えられないか検討したか
- [ ] h2 サイズ・見出しラベルのマージン・左右パディングがデッキ内で揃っているか（§6）
- [ ] 横並びカードの下端が揃っているか（§4-3）
- [ ] マーカーコメントが入っているか（§11）
- [ ] フォントのローカル代替が書かれているか（§12 の 20）
- [ ] 面ルールの許容枚数を超えていないか（§12-1）
- [ ] TODO ブロックがある場合、完了報告に一覧を列挙したか
