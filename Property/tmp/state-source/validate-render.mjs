import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const runtime = 'C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1112-737-0_26.1112.737.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules';
const mermaidDir = 'C:/Users/THANH NHAN/.codex/visualizations/2026/10/09/01a12053-fca1-7ce0-8a30-b494a648e9fc/review/mermaid_validation/node_modules/mermaid/dist';
const { chromium } = await import(pathToFileURL(path.join(runtime, 'playwright/index.mjs')));
const browser = await chromium.launch({
  executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  headless: true,
});
try {
  const page = await browser.newPage({ viewport: { width: 1800, height: 1100 }, deviceScaleFactor: 1 });
  await page.setContent('<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;background:white"><main style="display:inline-block;padding:24px"></main></body></html>');
  await page.addScriptTag({ path: path.join(mermaidDir, 'mermaid.js') });
  await page.evaluate(() => mermaid.initialize({ startOnLoad: false, securityLevel: 'strict' }));
  const folder = 'D:/3.Diagram/4.Submit_STATE';
  const files = (await fs.readdir(folder)).filter(name => name.endsWith('.mmd')).sort();
  if (files.length !== 4) throw new Error('Expected exactly four Mermaid files');
  for (const [index, file] of files.entries()) {
    const rawSource = await fs.readFile(path.join(folder, file), 'utf8');
    const source = process.argv.includes('--lr') ? rawSource.replace('direction TB', 'direction LR') : rawSource;
    const result = await page.evaluate(async ({ source, index }) => {
      await mermaid.parse(source);
      const { svg } = await mermaid.render(`stateDiagram${index}`, source);
      const main = document.querySelector('main');
      main.innerHTML = svg;
      const el = main.querySelector('svg');
      const view = el.viewBox.baseVal;
      el.style.maxWidth = 'none';
      el.style.width = Math.ceil(view.width) + 'px';
      el.style.height = Math.ceil(view.height) + 'px';
      const fonts = [...new Set([...el.querySelectorAll('text, .nodeLabel, .edgeLabel')].map(x => getComputedStyle(x).fontFamily))];
      if (fonts.some(font => !font.toLowerCase().includes('arial'))) throw new Error('Non-Arial label: ' + fonts.join(', '));
      const nodes = [...el.querySelectorAll('g.node')].filter(x => x.querySelector('rect.basic'));
      const centers = nodes.map(node => {
        const box = node.querySelector('rect.basic').getBoundingClientRect();
        const label = node.querySelector('g.label').getBoundingClientRect();
        return Math.abs((box.left + box.width / 2) - (label.left + label.width / 2));
      });
      if (centers.some(delta => delta > 2)) throw new Error('Off-center node text: ' + centers.join(', '));
      return { svg, width: Math.ceil(view.width), height: Math.ceil(view.height), fonts, maxCenterError: Math.max(0, ...centers) };
    }, { source, index });
    const stem = file.replace('.mmd', '') + (process.argv.includes('--lr') ? '-LR' : '');
    await fs.writeFile(`D:/3.Diagram/tmp/state-source/${stem}.svg`, result.svg, 'utf8');
    await page.locator('main').screenshot({ path: `D:/3.Diagram/tmp/state-source/${stem}.png` });
    console.log(JSON.stringify({ file, syntax: 'PASS', render: 'PASS', width: result.width, height: result.height, fonts: result.fonts, maxCenterError: result.maxCenterError }));
  }
} finally {
  await browser.close();
}
