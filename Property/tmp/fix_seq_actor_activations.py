import copy
import html
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
NS = {'s': 'http://www.w3.org/2000/svg'}


def group_span(svg, cell_id):
    start = svg.index(f'<g data-cell-id="{cell_id}">')
    depth = 0
    for tag in re.finditer(r'</?g\b[^>]*>', svg[start:]):
        depth += -1 if tag.group().startswith('</') else 1
        if depth == 0:
            return start, start + tag.end()
    raise AssertionError(cell_id)


def update_cell(text, cell_id, update):
    pattern = rf'<mxCell\b[^>]*\bid="{re.escape(cell_id)}"[^>]*>.*?</mxCell>'
    text, count = re.subn(pattern, lambda m: update(m.group()), text, flags=re.S)
    assert count == 1, (cell_id, count)
    return text


for file in Path('2.Submit_SEQ').glob('*.svg'):
    original = file.read_text(encoding='utf-8')
    svg = ET.fromstring(original)
    content_match = re.search(r'\bcontent="([^"]*)"', original)
    model_text = html.unescape(content_match[1])
    model = ET.fromstring(model_text)
    visible_ids = {n.get('data-cell-id') for n in svg.iter()}
    page = max(model.findall('diagram'), key=lambda d: len(visible_ids & {c.get('id') for c in d.findall('.//mxCell')}))
    cells = page.findall('.//mxCell')
    actor, = [c for c in cells if 'shape=umlActor;' in c.get('style', '')]
    geom = actor.find('mxGeometry')
    actor_x = float(geom.get('x')) + float(geom.get('width')) / 2
    lifeline, = [c for c in cells if c.get('edge') == '1'
                 and 'endArrow=none;' in c.get('style', '')
                 and float(c.find("mxGeometry/mxPoint[@as='sourcePoint']").get('x')) == actor_x]
    rendered_line = svg.find(f'.//s:g[@data-cell-id="{lifeline.get("id")}"]//s:path', NS)
    render_x, render_y = map(float, re.match(r'M ([\d.-]+) ([\d.-]+)', rendered_line.get('d')).groups())
    line_start = lifeline.find("mxGeometry/mxPoint[@as='sourcePoint']")
    dx, dy = render_x - actor_x, render_y - float(line_start.get('y'))
    frames = [c for c in cells if 'shape=umlFrame;' in c.get('style', '')]
    activations = [c for c in cells if c.get('vertex') == '1' and c.find('mxGeometry').get('width') == '10']
    template = activations[0]
    page_pattern = rf'<diagram\b[^>]*\bid="{re.escape(page.get("id"))}"[^>]*>.*?</diagram>'
    page_match = re.search(page_pattern, model_text, re.S)
    page_text = page_match.group()
    rendered = original[content_match.end():]
    new_cells, new_groups, changed_edges = [], [], []
    for index, frame in enumerate(frames, 1):
        fg = frame.find('mxGeometry')
        top, bottom = float(fg.get('y')), float(fg.get('y')) + float(fg.get('height'))
        endpoints = []
        for c in cells:
            if c.get('edge') != '1' or 'endArrow=none;' in c.get('style', ''):
                continue
            for point in c.findall('mxGeometry/mxPoint'):
                if float(point.get('x')) == actor_x and top <= float(point.get('y')) <= bottom:
                    endpoints.append((c, point))
        assert len(endpoints) >= 2
        start = min(float(p.get('y')) for _, p in endpoints)
        end = max(float(p.get('y')) for _, p in endpoints)
        cell_id = f'seq-actor-activation-{page.get("id")}-{index}'
        assert cell_id not in visible_ids
        cell = copy.deepcopy(template)
        cell.set('id', cell_id)
        cell.set('value', '')
        cell.find('mxGeometry').attrib.update(x=f'{actor_x-5:g}', y=f'{start:g}', width='10', height=f'{end-start:g}')
        new_cells.append(ET.tostring(cell, encoding='unicode').strip())
        new_groups.append(f'<g data-cell-id="{cell_id}"><g transform="translate(0.5,0.5)"><rect x="{actor_x-5+dx:g}" y="{start+dy:g}" width="10" height="{end-start:g}" fill="#ffffff" stroke="#555555" pointer-events="all" style="fill: light-dark(rgb(255, 255, 255), rgb(18, 18, 18)); stroke: light-dark(rgb(85, 85, 85), rgb(164, 164, 164));"/></g></g>')
        for edge, point in endpoints:
            role, edge_id = point.get('as'), edge.get('id')
            def update_point(block):
                pattern = rf'<mxPoint\b(?=[^>]*\bas="{role}")[^>]*/>'
                block, count = re.subn(pattern, lambda m: re.sub(r'\bx="[^"]*"', f'x="{actor_x+5:g}"', m.group()), block)
                assert count == 1
                return block
            page_text = update_cell(page_text, edge_id, update_point)
            a, b = group_span(rendered, edge_id)
            group = rendered[a:b]
            paths = 0
            def update_path(match):
                number_index = [0]
                def move_number(n):
                    k = number_index[0]
                    number_index[0] += 1
                    value = float(n.group())
                    if k % 2 == 0 and ((role == 'sourcePoint' and k == 0) or (role == 'targetPoint' and (paths > 0 or k >= 2))):
                        return f'{value+5:g}'
                    return n.group()
                return 'd="' + re.sub(r'-?\d+(?:\.\d+)?', move_number, match[1]) + '"'
            # Each edge uses a line path followed by its arrowhead path.
            parts = []
            cursor = 0
            for match in re.finditer(r'\bd="([^"]*)"', group):
                parts.extend([group[cursor:match.start()], update_path(match)])
                cursor = match.end()
                paths += 1
            parts.append(group[cursor:])
            rendered = rendered[:a] + ''.join(parts) + rendered[b:]
            changed_edges.append(edge_id)
    model_anchor = re.search(rf'<mxCell\b[^>]*\bid="{re.escape(template.get("id"))}"', page_text).start()
    page_text = page_text[:model_anchor] + '\n        '.join(new_cells) + '\n        ' + page_text[model_anchor:]
    model_text = model_text[:page_match.start()] + page_text + model_text[page_match.end():]
    render_anchor, _ = group_span(rendered, template.get('id'))
    rendered = rendered[:render_anchor] + ''.join(new_groups) + rendered[render_anchor:]
    encoded = html.escape(model_text, quote=True).replace('\n', '&#10;')
    updated = original[:content_match.start(1)] + encoded + '"' + rendered
    parsed = ET.fromstring(updated)
    updated_model = ET.fromstring(parsed.get('content'))
    for before, after in zip(model.findall('diagram'), updated_model.findall('diagram')):
        if before.get('id') != page.get('id'):
            assert ET.tostring(before) == ET.tostring(after)
    assert len(parsed.findall('.//s:g', NS)) == len(svg.findall('.//s:g', NS)) + 2*len(frames)
    assert [n.text for n in svg.iter() if n.tag.endswith('text')] == [n.text for n in parsed.iter() if n.tag.endswith('text')]
    file.write_text(updated, encoding='utf-8', newline='')
    print(f'{file.name}: {len(frames)} actor activation(s), {len(changed_edges)} message endpoints updated')
