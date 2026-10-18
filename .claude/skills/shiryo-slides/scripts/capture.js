#!/usr/bin/env node
/**
 * デッキ HTML の各 `.s` スライドを個別の PNG に書き出す。
 *
 * 使い方:
 *   node capture.js <html-path> <out-dir> [--only=N1,N2,...]
 *
 * 出力: <out-dir>/sNN.png（1 始まり・2 桁ゼロ埋め）
 *
 * 撮影にあたっての要点:
 *   1. Web フォントの読み込み完了を待ってから撮影する
 *   2. 意図したフォントが読めていない場合に警告を出す
 *      （CDN が塞がれた環境で代替フォントのまま撮影され、
 *        誰も気づかないまま「これが正しい見た目」になる事故を防ぐ）
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

function parseArgs(argv) {
  const positional = [];
  const flags = {};
  for (const a of argv) {
    if (a.startsWith('--only=')) {
      flags.only = a.slice('--only='.length).split(',').map(s => parseInt(s.trim(), 10));
    } else if (!a.startsWith('--')) {
      positional.push(a);
    }
  }
  return { positional, flags };
}

/**
 * ページが読もうとしている Google Fonts のファミリー名を列挙し、
 * 実際にその書体で描画されているかを判定する。
 *
 * 判定は canvas の実測幅で行う。`document.fonts.check()` は該当する
 * @font-face が存在しない場合も true を返す（フォールバックで描画できる
 * とみなすため）ので、この用途には使えない。
 *
 * 幅比較なら「CDN 経由・ローカル導入済みのどちらでも、意図した書体で
 * 描画されていれば OK」と判定できる。知りたいのは CDN の到達可否ではなく
 * 見た目が意図通りかどうかなので、こちらが正しい問い。
 *
 * @returns {Promise<{intended: string[], missing: string[]}>}
 */
async function checkFonts(page) {
  return page.evaluate(async () => {
    // <link> から読もうとしているファミリー名を集める
    const declared = new Set();
    document.querySelectorAll('link[href*="fonts.googleapis.com"]').forEach((link) => {
      const url = new URL(link.href);
      url.searchParams.getAll('family').forEach((spec) => {
        const name = spec.split(':')[0].replace(/\+/g, ' ').trim();
        if (name) declared.add(name);
      });
    });

    try { await document.fonts.ready; } catch (_) { /* 進行を止めない */ }

    // 実際に要素で使われているファミリーだけを対象にする。
    // 宣言だけされて使われていないファミリーはダウンロードされず、
    // 「読めていない」と判定されてしまうため（誤警告の元）
    const used = new Set();
    document.querySelectorAll('*').forEach((el) => {
      const ff = getComputedStyle(el).fontFamily || '';
      declared.forEach((name) => { if (ff.includes(name)) used.add(name); });
    });

    // 判定は欧文のみのサンプルで行う。
    // 和文は全角でどのフォントでも字幅が同じになり、判別できない（実測で確認）
    const ctx = document.createElement('canvas').getContext('2d');
    const sample = 'ABCDEFGHIJ abcdefghij 0123456789';
    const measure = (stack) => { ctx.font = `40px ${stack}`; return ctx.measureText(sample).width; };
    const baseline = measure('monospace');
    const intended = [...used];
    const missing = intended.filter((name) => measure(`"${name}", monospace`) === baseline);
    return { intended, missing };
  });
}

(async () => {
  const { positional, flags } = parseArgs(process.argv.slice(2));
  if (positional.length < 2) {
    console.error('Usage: node capture.js <html-path> <out-dir> [--only=N1,N2,...]');
    process.exit(1);
  }
  const [htmlPath, outDir] = positional;
  fs.mkdirSync(outDir, { recursive: true });

  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 960, height: 540 },
    deviceScaleFactor: 1,
  });
  const page = await ctx.newPage();
  await page.goto('file://' + path.resolve(htmlPath), { waitUntil: 'load' });

  // Web フォントが届くのを待つ。CDN が塞がれている環境では
  // networkidle が来ないことがあるためタイムアウトを飲み込む。
  await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});

  const { intended, missing } = await checkFonts(page);
  if (missing.length > 0) {
    console.warn('');
    console.warn('  警告: 以下の Web フォントが読み込めていません。');
    missing.forEach(name => console.warn(`         - ${name}`));
    console.warn('  代替フォントで撮影されるため、意図した見た目と異なります。');
    console.warn('  （社内プロキシで Google Fonts が塞がれている / オフラインの可能性）');
    console.warn('');
  } else if (intended.length > 0) {
    console.log(`フォント読み込み OK: ${intended.join(', ')}`);
  }

  const total = await page.evaluate(() => document.querySelectorAll('.s').length);
  if (total === 0) {
    console.error('HTML 内に .s 要素が見つかりません');
    await browser.close();
    process.exit(2);
  }

  const targets = flags.only
    ? flags.only.filter(n => n >= 1 && n <= total).map(n => n - 1)
    : Array.from({ length: total }, (_, i) => i);

  for (const i of targets) {
    await page.evaluate((idx) => {
      const all = document.querySelectorAll('.s');
      all.forEach((el, j) => {
        el.classList.toggle('active', j === idx);
        el.style.transform = 'translate(-50%, -50%) scale(1)';
      });
    }, i);
    const filename = `s${String(i + 1).padStart(2, '0')}.png`;
    await page.screenshot({
      path: path.join(outDir, filename),
      clip: { x: 0, y: 0, width: 960, height: 540 },
    });
  }

  console.log(`${targets.length} 枚を ${outDir} に書き出しました`);
  await browser.close();
})().catch(err => {
  console.error(err);
  process.exit(1);
});
