// Render a page frame-by-frame using its window.__renderAt(t) hook.
// usage: node tools/render-frames.js <page.html relative to repo> <outDir> [fps=30] [width=1080] [height=1920] [stills: t1 t2 ...]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const [pagePath, out, fps = '30', W = '1080', H = '1920', ...stills] = process.argv.slice(2);
const types = { '.html': 'text/html', '.js': 'text/javascript' };
const server = http.createServer((req, res) => {
  let f = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (f.endsWith('/')) f += 'index.html';
  fs.readFile(f, (e, d) => { if (e) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); res.end(d); });
}).listen(0, async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const page = await browser.newPage({ viewport: { width: W / 2, height: H / 2 }, deviceScaleFactor: 2 });
  page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto(`http://localhost:${server.address().port}/${pagePath}?render=1`);
  await page.waitForFunction('window.__ready === true', null, { timeout: 30000 });
  fs.mkdirSync(out, { recursive: true });
  const dur = await page.evaluate('window.__DURATION');
  const list = stills.length ? stills.map(Number) : Array.from({ length: Math.round(dur * fps) }, (_, i) => i / fps);
  let i = 0;
  for (const t of list) {
    await page.evaluate(t => window.__renderAt(t), t);
    const name = stills.length ? `t${t}.png` : `f${String(i).padStart(5, '0')}.jpg`;
    await page.screenshot({ path: path.join(out, name), ...(stills.length ? {} : { type: 'jpeg', quality: 92 }) });
    if (++i % 100 === 0) console.log('frame', i, '/', list.length);
  }
  await browser.close(); server.close();
});
