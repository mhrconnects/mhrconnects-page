// usage: node render.js <repoDir> <outDir> <fps> [times...]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const [root, out, fpsArg, ...times] = process.argv.slice(2);
const types = { '.html': 'text/html', '.js': 'text/javascript' };
const server = http.createServer((req, res) => {
  const f = path.join(root, decodeURIComponent(req.url.split('?')[0]).replace(/\/$/, '/index.html'));
  fs.readFile(f, (e, d) => { if (e) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' }); res.end(d); });
}).listen(0, async () => {
  const port = server.address().port;
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('console', m => console.log('console:', m.text())); page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto(`http://localhost:${port}/?render=1`);
  await page.waitForFunction('window.__ready === true', null, { timeout: 30000 });
  fs.mkdirSync(out, { recursive: true });
  const fps = +fpsArg;
  const list = times.length ? times.map(Number) : Array.from({ length: Math.round(36 * fps) + Math.round(2*fps) }, (_, i) => i / fps);
  let i = 0;
  for (const t of list) {
    await page.evaluate(t => window.__renderAt(t), t);
    await page.screenshot({ path: path.join(out, times.length ? `t${t}.png` : `f${String(i).padStart(5, '0')}.jpg`), ...(times.length ? {} : { type: 'jpeg', quality: 92 }) });
    if (++i % 100 === 0) console.log('frame', i, '/', list.length);
  }
  await browser.close(); server.close();
});
