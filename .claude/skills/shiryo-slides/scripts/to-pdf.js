#!/usr/bin/env node
/**
 * デッキ HTML（`.s` スライド要素を持つ）を PDF に変換する。
 * 1 スライド = 1 ページ、960×540（16:9）。
 *
 * 使い方:
 *   node to-pdf.js <html-path> <output-pdf-path>
 *
 * 仕組み:
 * - 印刷用スタイルを注入し、全 `.s` を可視化してページ区切りを入れる。
 *   印刷モードでは元の JS ナビゲーションはバイパスされる。
 * - PDF のページサイズはスライドの設計キャンバスに合わせて 960×540px 固定。
 */
const path = require('path');
const fs = require('fs');

function requirePlaywright() {
  try { return require('playwright'); } catch (_) {}
  try {
    const globalRoot = require('child_process').execSync('npm root -g', { encoding: 'utf8' }).trim();
    if (globalRoot && !module.paths.includes(globalRoot)) module.paths.push(globalRoot);
    return require('playwright');
  } catch (e) {
    console.error('playwright が見つかりません。以下でインストールしてください:');
    console.error('  npm install -g playwright && npx playwright install chromium');
    process.exit(1);
  }
}
const { chromium } = requirePlaywright();

(async () => {
  const [htmlPath, outPath] = process.argv.slice(2);
  if (!htmlPath || !outPath) {
    console.error('Usage: node to-pdf.js <html-path> <output-pdf-path>');
    process.exit(1);
  }

  const absHtml = path.resolve(htmlPath);
  const absOut = path.resolve(outPath);

  if (!fs.existsSync(absHtml)) {
    console.error(`HTML が見つかりません: ${absHtml}`);
    process.exit(1);
  }

  fs.mkdirSync(path.dirname(absOut), { recursive: true });

  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 960, height: 540 },
    deviceScaleFactor: 2,
  });
  const page = await ctx.newPage();
  await page.goto('file://' + absHtml, { waitUntil: 'networkidle' });

  // Web フォント（Google Fonts）の読み込みを待つ
  await page.evaluate(() => document.fonts && document.fonts.ready);

  const total = await page.evaluate(() => document.querySelectorAll('.s').length);
  if (total === 0) {
    console.error('HTML 内に .s 要素が見つかりません');
    await browser.close();
    process.exit(2);
  }

  // 印刷用 CSS を注入する:
  //  - 実行時 transform を打ち消して各スライドを 960×540 で描画
  //  - スライドごとに強制改ページ
  //  - @page サイズをスライドのキャンバスに一致させる
  //
  // 既知のバグ（対処済み・消さないこと）:
  // このスタイルシートは以前 `.s { display: block !important }` も指定して
  // 全スライドを可視化していた。テーマによって非アクティブスライドの隠し方は
  // visibility:hidden+opacity:0 だったり display:none だったりするためだが、
  // この一括 display:block は、スライドのルート要素が inline の display:flex に
  // 依存しているデッキ（flex:1 の子要素による縦センタリング、横ゾーン分割など）を
  // 静かに破壊する。親が block に強制された時点で flex:1 も justify-content も
  // 無効になるため。
  // 対処: このスタイルシートでは display に触れない。代わりに各 `.s` の
  // 「実際に表示されるときの display 値」を要素ごとに読み取り、
  // emulateMedia('print') の直後にインラインで再適用する（後述の evaluate ブロック）。
  await page.addStyleTag({
    content: `
      @page { size: 960px 540px; margin: 0 }
      @media print {
        html, body {
          width: 960px;
          height: auto;
          min-height: 0;
          background: #fff;
          overflow: visible;
        }
        body > script { display: none }
        .s {
          visibility: visible !important;
          opacity: 1 !important;
          position: relative !important;
          top: auto !important;
          left: auto !important;
          transform: none !important;
          margin: 0 !important;
          width: 960px !important;
          height: 540px !important;
          page-break-after: always;
          break-after: page;
          overflow: hidden;
        }
        .s:last-child {
          page-break-after: auto;
          break-after: auto;
        }
      }
    `,
  });

  // page.pdf() の中で @media print ブロックが効くように印刷メディアを強制する
  await page.emulateMedia({ media: 'print' });

  // 一括 display:block ではなく、各スライドを「それ自身の正しい display 値」で
  // 可視化する（上の既知バグ注記を参照）。
  //
  // 各 `.s` について active クラスを一時的に付け（テーマ側のスライド表示・非表示は
  // このクラスをキーにしている）、その結果の computed display を読んでから
  // クラスを元に戻す。デッキ自身の active 管理を壊さないため。
  // 読み取った値（"flex" / "block" / "grid" など）をインラインスタイルに
  // !important 付きで書き戻すことで:
  //   - display:none で非アクティブを隠すテーマでも全スライドが可視化され、
  //   - スライドのルートが flex に依存するテーマでもレイアウトが保たれる。
  // visibility / opacity も念のためインラインで固定する。
  await page.evaluate(() => {
    document.querySelectorAll('.s').forEach((el) => {
      const wasActive = el.classList.contains('active');
      if (!wasActive) el.classList.add('active');
      const display = getComputedStyle(el).display;
      if (!wasActive) el.classList.remove('active');

      el.style.setProperty('display', display, 'important');
      el.style.setProperty('visibility', 'visible', 'important');
      el.style.setProperty('opacity', '1', 'important');
    });
  });

  // 重要: 全スライドを可視化した「後」にもう一度フォントを待つ。
  // Google Fonts は CJK フォントを多数の unicode-range サブセットに分割して配信し、
  // 実際にそのグリフが描画されるときに初めてダウンロードされる。
  // display:none で非アクティブを隠すテーマでは、この時点で 1 枚目に使われた
  // サブセットしか読み込まれていない。全スライドを可視化すると新たな
  // サブセット要求の波が発生し、それが終わる前に PDF 化すると該当グリフだけ
  // システムフォントにフォールバックする（1 つの見出しの中で細字と擬似ボールドが
  // 混ざる、という症状で出る）。
  await page.waitForTimeout(300); // 新しいサブセット要求が始まるのを待つ
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => document.fonts && document.fonts.ready);
  await page.waitForFunction(() => !document.fonts || document.fonts.status === 'loaded');

  await page.pdf({
    path: absOut,
    width: '960px',
    height: '540px',
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: '0', right: '0', bottom: '0', left: '0' },
  });

  await browser.close();

  // 生成された PDF の「実際の」ページ数を検証する。
  // スライド枚数をページ数として報告してはいけない。印刷 CSS が
  // 非表示スライドの可視化に失敗すると、PDF が静かに 1 ページになる。
  const pdfData = fs.readFileSync(absOut);
  const actualPages = (pdfData.toString('latin1').match(/\/Type\s*\/Page[^s]/g) || []).length;

  const stat = fs.statSync(absOut);
  const sizeKb = (stat.size / 1024).toFixed(1);

  if (actualPages !== total) {
    console.error(
      `エラー: スライド枚数 (${total}) と PDF ページ数 (${actualPages}) が一致しません。` +
      `テーマのスライド非表示 CSS が印刷 CSS で上書きできていない可能性があります。` +
      `確認用に ${absOut} は残しますが、この実行は失敗として扱ってください。`
    );
    process.exit(3);
  }

  console.log(`${absOut} を生成しました（${actualPages} ページ検証済み・${sizeKb} KB）`);
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
