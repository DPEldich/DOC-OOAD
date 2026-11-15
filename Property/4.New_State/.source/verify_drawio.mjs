import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';

const runtime = 'C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1112-737-0_26.1112.737.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules';
const { chromium } = await import(pathToFileURL(path.join(runtime, 'playwright/index.mjs')));
const response = await fetch('https://viewer.diagrams.net/js/viewer-static.min.js');
assert(response.ok, 'Cannot load official diagrams.net viewer');
const viewer = await response.text();
const root = path.resolve('4.New_State');
const browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1800, height: 1500 } });
  await page.setContent('<html><head><meta charset="utf-8"></head><body style="margin:0;background:white"></body></html>');
  await page.addScriptTag({ content: viewer });
  const results = [];
  for (const code of ['KH', 'NCC', 'PLSP', 'XT']) {
    const xml = await fs.readFile(path.join(root, 'Nguon_drawio', code + '.drawio'), 'utf8');
    const result = await page.evaluate(({ xml }) => {
      document.body.innerHTML = '<div id="preview" style="width:1740px;margin:20px"></div>';
      const doc = mxUtils.parseXml(xml);
      const model = doc.getElementsByTagName('mxGraphModel')[0];
      const div = document.getElementById('preview');
      const graph = new Graph(div);
      graph.setEnabled(false);
      graph.setHtmlLabels(true);
      const codec = new mxCodec(model.ownerDocument);
      codec.decode(model, graph.getModel());
      graph.view.validate();
      const bounds = graph.getGraphBounds();
      div.style.height = Math.ceil(bounds.height + 40) + 'px';
      return { cells: Object.keys(graph.getModel().cells).length, vertices: Object.values(graph.getModel().cells).filter(c => c.vertex).length,
        edges: Object.values(graph.getModel().cells).filter(c => c.edge).length,
        width: bounds.width, height: bounds.height, hasSvg: !!div.querySelector('svg') };
    }, { xml });
    assert(result.hasSvg && result.vertices > 10 && result.edges > 0, 'Draw.io import failed');
    await page.screenshot({ path: path.join(root, '.source', 'drawio-' + code + '.png'), fullPage: true });
    results.push({ code, import: 'pass', ...result });
  }
  await fs.writeFile(path.join(root, '.source/drawio-verification.json'), JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results));
} finally {
  await browser.close();
}
