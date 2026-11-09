// shoot.mjs — screenshot reali delle scene dichiarate in scenes.json.
// Usa playwright-core con il Chrome gia' installato: nessun download di browser.
// (In WSL non si punta mai al Chrome di Windows: /mnt/c e' lento e CDP attraversa la VM.)
import { createRequire } from 'node:module';
import { readFileSync, mkdirSync, readdirSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';

// require (non import) perche' rispetta NODE_PATH: cosi' playwright-core puo' stare
// in un node_modules del progetto video invece che dentro la skill.
const require = createRequire(import.meta.url);
const { chromium } = require('playwright-core');

// Percorso locale o URL: il #hash si conserva (per i file serve un file:// vero).
function targetOf(u) {
  const [path, hash = ''] = u.split('#');
  return /^https?:/.test(path) ? u : pathToFileURL(resolve(path)).href + (hash ? `#${hash}` : '');
}

// CHROME_BIN vince; poi la chrome-headless-shell piu' recente in cache puppeteer; poi il chrome normale.
function findChrome() {
  if (process.env.CHROME_BIN) return process.env.CHROME_BIN;
  const root = join(process.env.HOME, '.cache/puppeteer');
  const candidates = [];
  for (const kind of ['chrome-headless-shell', 'chrome']) {
    const dir = join(root, kind);
    if (!existsSync(dir)) continue;
    for (const build of readdirSync(dir).sort().reverse()) {
      candidates.push(
        join(dir, build, kind === 'chrome' ? 'chrome-linux64/chrome' : 'chrome-headless-shell-linux64/chrome-headless-shell'),
      );
    }
  }
  const found = candidates.find((p) => existsSync(p));
  if (!found) {
    console.error('Nessun Chrome in ~/.cache/puppeteer: imposta CHROME_BIN o installa con');
    console.error('  npx @puppeteer/browsers install chrome-headless-shell@stable --path ~/.cache/puppeteer');
    process.exit(2);
  }
  return found;
}

const browser = await chromium.launch({ executablePath: findChrome(), args: ['--no-sandbox', '--hide-scrollbars'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });

// --probe <url|pagina> [...] : esplorazione, prima di scrivere scenes.json.
// Uno screenshot per pagina in video/probe/ e le coordinate dei blocchi chiave: gli zoom e i
// cerchietti si ricavano da qui, non a occhio sulla foto (3 render buttati per questo).
const probeAt = process.argv.indexOf('--probe');
if (probeAt >= 0) {
  const urls = process.argv.slice(probeAt + 1);
  if (!urls.length) {
    console.error('uso: shoot.mjs --probe <url|pagina.html> [...]');
    process.exit(2);
  }
  const out = resolve('video/probe');
  mkdirSync(out, { recursive: true });
  for (const [i, u] of urls.entries()) {
    await page.goto('about:blank');
    await page.goto(targetOf(u), { waitUntil: 'networkidle' });
    const name = (u.split('#')[0].split('?')[0].split('/').filter(Boolean).pop() || `p${i + 1}`)
      .replace(/\.\w+$/, '').replace(/[^\w.-]/g, '_');
    const file = resolve(out, `${String(i + 1).padStart(2, '0')}-${name}.png`);
    await page.screenshot({ path: file });
    // Blocchi che nella pratica si evidenziano: titoli, riga KPI, filtri.
    const pts = await page.evaluate(() => [...document.querySelectorAll('h1, h2, #kpi > *, #filters > *')]
      .slice(0, 40).map(el => {
        const r = el.getBoundingClientRect();
        return {
          el: el.tagName.toLowerCase() + (el.id ? `#${el.id}` : ''),
          txt: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 28),
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
        };
      }));
    console.log(`probe ${name} -> ${file}`);
    for (const p of pts) console.log(`  ${p.el} "${p.txt}" cx=${p.cx} cy=${p.cy}`);
  }
  await browser.close();
  process.exit(0);
}

const cfgPath = process.argv[2] || 'scenes.json';
const cfg = JSON.parse(readFileSync(cfgPath, 'utf8'));
const outDir = resolve('video/assets');
mkdirSync(outDir, { recursive: true });

for (const s of cfg.scenes) {
  // Navigazione hash-only non ricarica: azzera, o la scena eredita lo stato della precedente.
  await page.goto('about:blank');
  await page.goto(targetOf(s.url), { waitUntil: 'networkidle' });
  for (const step of s.steps || []) {
    if (step.click) await page.click(step.click);
    if (step.fill) await page.fill(step.fill[0], step.fill[1]);
    if (step.press) await page.keyboard.press(step.press);
    if (step.wait) await page.waitForTimeout(step.wait);
  }
  const file = resolve(outDir, `${s.id}.png`);
  await page.screenshot({ path: file });
  console.log(`shot ${s.id} -> ${file}`);
}
await browser.close();
