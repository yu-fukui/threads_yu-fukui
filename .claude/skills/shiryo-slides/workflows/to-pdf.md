# to-pdf モード手順書

既存の `slides/*.html` を、1 スライド = 1 ページの 16:9 PDF（960×540）に変換する。

**ユーザーが明示的に指示した時だけ実行する。**「PDF にして」「PDF 化」「PDF で出力」「PDF 版が欲しい」と言われた場合に限る。`quick` / `full` の完了後に気を利かせて PDF を作らない（`SKILL.md` §5 / §10）。
新規スライドは作らない。読むのはこのファイルと `core/validation.md` §1 だけで足りる。

---

## フェーズ A: 対象 HTML の特定

```bash
ls slides/*.html 2>/dev/null
```

| 見つかった数 | 対応 |
|---|---|
| 1 個 | それを使う。確認しない |
| 複数 | **1 問だけ**確認する |
| 0 個 | エラー報告し、quick / full へ誘導する |

> `slides/` に複数の HTML があります。どれを PDF にしますか（support-ai-proposal.html / kickoff-internal.html）。

---

## フェーズ B: Playwright 確認

PDF 化も Playwright を使う。`core/validation.md` §1 と同じ確認を行う。

```bash
node -e "require('playwright')" 2>/dev/null \
  || NODE_PATH="$(npm root -g 2>/dev/null)" node -e "require('playwright')" 2>/dev/null \
  || echo "NEED_INSTALL"
```

何も出力されなければ次へ。`NEED_INSTALL` が出たときだけ `npm install -g playwright && npx playwright install chromium` を案内して承認を得る。

**視覚検証と違い、PDF 化は Playwright 無しでは成立しない。** 未導入なら PDF は作れないと伝えて止まる。なお `scripts/to-pdf.js` はグローバル npm root を自動解決するので、フェーズ C の呼び出しに `NODE_PATH` は不要。

---

## フェーズ C: PDF 生成

```bash
node "<スキルルート>/scripts/to-pdf.js" "slides/<name>.html" "slides/<name>.pdf"
```

第 1 引数が入力 HTML、第 2 引数が出力 PDF。別名の指定がなければ HTML と同名で拡張子だけ `.pdf` にする。

スクリプトの挙動:

- ヘッドレス Chromium で開き、Web フォントの読み込みを待つ
- 印刷用 CSS を注入し、`transform` を打ち消して各スライドを 960×540 で描画、1 枚ごとに改ページ
- 全 `.s` を可視化する。`display` は一律上書きせず、**スライドごとに本来の表示時の値を読み取ってインライン適用する**（`display:flex` に依存するデッキを壊さないため）
- **全スライドを可視化した後にもう一度フォントの読み込みを待つ**（フェーズ E）
- 生成後に **PDF の実ページ数を検証**し、`.s` の枚数と一致しなければ **exit 3** で失敗させる

成功時のログ:

```
/abs/path/slides/<name>.pdf を生成しました（12 ページ検証済み・842.3 KB）
```

`ページ検証済み` は生成後の PDF から実測した値で、スライド枚数の転記ではない。**この数字をそのまま報告する。**

---

## フェーズ D: exit 3（ページ数不一致）の切り分け

exit 3 は「PDF はできたがページ数が合っていない」状態。**成功として報告しない。**
多くは 1 ページだけの PDF になっており、原因は**テーマのスライド非表示 CSS を印刷 CSS で上書きできていない**こと。

1. **`.s` の隠し方を確認する** — `grep -nE '\.s\s*\{[^}]*(visibility|opacity|display)' slides/<name>.html`。`core/rules.md` §11 のとおり `visibility:hidden` ＋ `opacity:0` になっているか。`display:none` で隠していても `to-pdf.js` は可視化できるが、**`!important` 付きの独自ルールや、`.s` 以外のクラスで隠している場合は上書きが届かない**

2. **`.s` がトップレベルにあるか** — 別の `div` で包んでその親を隠していると、全枚可視化が効かない

3. **枚数を実測して突き合わせる** — `grep -c '<div class="s' slides/<name>.html` がログの「スライド枚数」と一致するか。`.s` を含む別用途の要素が混ざっていないか

4. 1・2 に該当したら**HTML 側を直す。** 隠し方を `core/rules.md` §11 の形に戻してから再実行する

残った PDF は確認用で、**中身が不完全なので納品に使わない。**

---

## フェーズ E: フォント欠けの扱い

`capture.js` の撮影時に出るフォント問題は、PDF でも同じように起きる。

Google Fonts の CJK ファミリーは `unicode-range` でサブセット分割配信されており、**実際に描画された文字の分だけ遅延ダウンロードされる。**
非アクティブスライドを隠している間は 1 枚目に使われたサブセットしか届いていないため、全スライドを可視化した瞬間に新しいサブセット要求の波が起きる。これを待たずに PDF 化すると、**同じ見出しの中で太さがばらつく**（一部の文字だけシステムフォントに落ちる）。

`to-pdf.js` はこれを踏まえ、全スライド可視化の**後に**もう一度フォント読み込み完了を待つ実装になっている。それでも文字が別書体に見える場合は、フォントが届いていない環境を疑う。

1. `grep -n 'fonts.googleapis.com\|--ff' slides/<name>.html` で `<link>` と `--ff` / `--ff-en` を確認する
2. `--ff` / `--ff-en` の後半にローカル代替が並んでいるか。無ければ足す（テーマ定義の値が正）
3. `<link>` が書けているのに落ちるならネットワーク側（社内プロキシ / オフライン）。**レイアウトを調整しない。** 完了報告に明記する

   > Web フォントが取得できない環境のため、PDF は代替フォントで出力されています。
   > フォントが届く環境では見た目が変わります。

---

## フェーズ F: 完了報告

**ページ数とファイルパスを必ず書く。**

> `slides/<name>.pdf` を生成しました（12 ページ / 約 842 KB）。
> `open slides/<name>.pdf` で確認できます。

ページ数はスクリプトが実測した `ページ検証済み` の値を使う。フォント欠けがあった場合はフェーズ E の文面を添える。（`open` は macOS。Linux は `xdg-open`、Windows は `start`）

---

## このモードでやらないこと

- スライドの内容修正・追加 → `edit` ／ 新規スライド生成 → `quick` / `full`
- PNG の書き出し → `core/validation.md` の `capture.js`
- PowerPoint 形式への変換（このキットの対象外。`SKILL.md` §7）

PDF 化の途中で修正依頼が来たら、先に `edit` を完了させてから PDF を出し直す。
