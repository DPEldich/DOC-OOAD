import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';

const root = path.resolve('4.New_State');
const runtime = 'C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1112-737-0_26.1112.737.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules';
const { chromium } = await import(pathToFileURL(path.join(runtime, 'playwright/index.mjs')));
const diagrams = JSON.parse(await fs.readFile(path.join(root, '.source/diagrams.json'), 'utf8'));
const browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
const results = [];
try {
  const page = await browser.newPage({ deviceScaleFactor: 1.5 });
  for (const diagram of diagrams) {
    await page.setViewportSize({ width: diagram.size[0], height: diagram.size[1] });
    await page.goto(pathToFileURL(path.join(root, diagram.code + '.drawio.svg')).href);
    await page.evaluate(() => document.fonts.ready);
    const errors = await page.evaluate(() => {
      const errors = [];
      const box = el => { const b = el.getBBox(); return { x: b.x, y: b.y, width: b.width, height: b.height }; };
      const fits = (inner, outer, pad = 0) => inner.x >= outer.x + pad - 1 && inner.y >= outer.y + pad - 1 &&
        inner.x + inner.width <= outer.x + outer.width - pad + 1 && inner.y + inner.height <= outer.y + outer.height - pad + 1;
      const overlaps = (a, b) => a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
      const states = [...document.querySelectorAll('[data-state]')];
      const bounds = states.map(s => ({ id: s.dataset.state, ...box(s.querySelector('rect')) }));
      for (const state of states) {
        const outer = box(state.querySelector('rect'));
        for (const text of state.querySelectorAll('text')) {
          if (!fits(box(text), outer, 10)) errors.push('State text outside ' + state.dataset.state + ': ' + text.textContent);
        }
      }
      for (const label of document.querySelectorAll('[data-edge-label]')) {
        const outer = box(label.querySelector('rect'));
        for (const text of label.querySelectorAll('text')) {
          if (!fits(box(text), outer, 1)) errors.push('Label text outside ' + label.dataset.edgeLabel);
        }
        for (const state of bounds) if (overlaps(outer, state)) errors.push('Label touches state: ' + label.dataset.edgeLabel + ' / ' + state.id);
        for (const route of document.querySelectorAll('polyline[data-edge]')) {
          const pts = [...route.points].map(p => [p.x, p.y]);
          for (let i = 1; i < pts.length; i++) {
            const [a, b] = [pts[i - 1], pts[i]];
            const hit = a[0] === b[0]
              ? a[0] > outer.x && a[0] < outer.x + outer.width && Math.max(a[1], b[1]) > outer.y && Math.min(a[1], b[1]) < outer.y + outer.height
              : a[1] > outer.y && a[1] < outer.y + outer.height && Math.max(a[0], b[0]) > outer.x && Math.min(a[0], b[0]) < outer.x + outer.width;
            if (hit) errors.push('Label obscures route: ' + label.dataset.edgeLabel + ' / ' + route.dataset.edge);
          }
        }
      }
      const note = document.querySelector('[data-note]');
      const noteBounds = box(note.querySelector('path'));
      for (const text of note.querySelectorAll('text')) if (!fits(box(text), noteBounds, 10)) errors.push('Note text outside: ' + text.textContent);
      for (const text of document.querySelectorAll('text')) if (text.textContent.includes('�')) errors.push('Broken Unicode');
      return errors;
    });
    assert.deepEqual(errors, [], diagram.code + ' layout defects');
    for (const e of diagram.edges) {
      for (let i = 1; i < e.points.length; i++) {
        const [a, b] = [e.points[i - 1], e.points[i]];
        assert(a[0] === b[0] || a[1] === b[1], 'Non-orthogonal segment');
        for (const s of diagram.states.filter(s => s.id !== e.source && s.id !== e.target)) {
          const hit = a[0] === b[0]
            ? a[0] > s.x && a[0] < s.x + s.w && Math.max(a[1], b[1]) > s.y && Math.min(a[1], b[1]) < s.y + s.h
            : a[1] > s.y && a[1] < s.y + s.h && Math.max(a[0], b[0]) > s.x && Math.min(a[0], b[0]) < s.x + s.w;
          assert(!hit, `${diagram.code}: ${e.id} crosses ${s.id}`);
        }
      }
    }
    await page.locator('svg').screenshot({ path: path.join(root, 'PNG', diagram.code + '.png') });
    results.push({ code: diagram.code, svgXml: 'pass', textFit: 'pass', labelsClear: 'pass', orthogonalRoutes: 'pass', unrelatedNodesClear: 'pass', png: `PNG/${diagram.code}.png` });
  }
  await page.goto(pathToFileURL(path.join(root, 'index.html')).href);
  for (const width of [1440, 760]) {
    await page.setViewportSize({ width, height: 1000 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'Overview horizontal overflow');
  }
  for (const href of await page.locator('a').evaluateAll(a => a.map(el => el.getAttribute('href')))) {
    if (href.startsWith('#')) assert(await page.locator(href).count(), 'Missing overview anchor');
    else await fs.access(path.join(root, decodeURIComponent(href)));
  }
  await fs.writeFile(path.join(root, '.source/verification.json'), JSON.stringify({ diagrams: results, overviewLinks: 'pass', overviewResponsive: 'pass' }, null, 2));
  console.log(JSON.stringify(results));
} finally {
  await browser.close();
}
