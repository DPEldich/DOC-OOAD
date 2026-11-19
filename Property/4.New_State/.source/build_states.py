from pathlib import Path
from html import escape
import json
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
BLUE = '#303f92'
INK = '#222222'


def state(sid, x, y, w, h, title, description, attribute, lines):
    return dict(id=sid, x=x, y=y, w=w, h=h, title=title,
                description=description, attribute=attribute, lines=lines)


def edge(eid, source, target, points, label, at, width=550):
    return dict(id=eid, source=source, target=target, points=points,
                label=label, at=at, width=width)


DIAGRAMS = [
    dict(code='KH', name='Khách hàng', size=(1480, 860),
         subtitle='Đối tượng: một hồ sơ khách hàng | Góc nhìn: tình trạng lưu hồ sơ | Người thao tác: NV',
         initial=(300, 140),
         states=[
             state('draft', 80, 250, 440, 255, 'DRAFT', 'Chưa lưu hồ sơ', 'customerState = DRAFT', [
                 'entry / khởi tạo hồ sơ khách hàng tạm',
                 'nhậpThôngTin(tt) / cập nhật bản tạm',
                 'lưu() [thông tin không hợp lệ]',
                 '    / báo lỗi; giữ hồ sơ tạm',
             ]),
             state('saved', 950, 250, 450, 325, 'SAVED', 'Đã lưu hồ sơ', 'customerState = SAVED', [
                 'traCứu(từKhóa) / trả thông tin khách hàng',
                 'cậpNhật(tt) [thông tin hợp lệ]',
                 '    / lưu họ tên, số điện thoại',
                 'cậpNhật(tt) [thông tin không hợp lệ]',
                 '    / báo lỗi; giữ thông tin đã lưu',
             ]),
         ],
         edges=[
             edge('create', 'initial', 'draft', [(300, 152), (300, 250)],
                  ['tạoHồSơKhách()', '[khách mới khi lập đơn]'], (525, 186), 430),
             edge('save', 'draft', 'saved', [(520, 375), (950, 375)],
                  ['lưu()', '[thông tin hợp lệ]', '/ lưu hồ sơ vào CSDL'], (735, 310), 400),
         ],
         note=(60, 660, 1360, 155),
         notes=[
             'Ký hiệu: sự kiện(tham số) [điều kiện] / hành động; xử lý ghi trong khung không làm đổi trạng thái.',
             'Khách mới được ghi nhận trong luồng lập đơn; phân hệ Khách hàng hiện có tra cứu và cập nhật.',
             'Tra cứu, sửa thông tin hợp lệ hoặc báo lỗi đều giữ trạng thái SAVED.',
             'Không vẽ nút kết thúc: phạm vi hiện có chưa quy định xóa hoặc chấm dứt hồ sơ khách hàng.',
         ],
         sources='Nguồn nghiệp vụ: UC-KH, SEQ-KH, ACT-KH; luồng thêm khách khi lập đơn theo mô hình hiện có.',
         main=['draft', 'saved'],
         types={'draft': 'start', 'saved': 'active'}),
    dict(code='NCC', name='Nhà cung cấp', size=(1680, 1080),
         subtitle='Đối tượng: một nhà cung cấp | Góc nhìn: tình trạng sử dụng và nguồn cung sản phẩm',
         initial=(305, 130),
         states=[
             state('empty', 90, 250, 430, 300, 'NO_PRODUCTS', 'Chưa có sản phẩm cung ứng', 'supplierState = NO_PRODUCTS', [
                 'Số liên kết sản phẩm = 0',
                 'cậpNhật(tt) [hợp lệ] / lưu thông tin',
                 'traCứu(từKhóa) / trả thông tin NCC',
                 'xóaNCC() [đã có phiếu nhập]',
                 '    / từ chối; giữ nguyên trạng thái',
             ]),
             state('supplying', 1120, 250, 470, 345, 'SUPPLYING', 'Đang cung cấp sản phẩm', 'supplierState = SUPPLYING', [
                 'Số liên kết sản phẩm > 0',
                 'thêmSP(sp) [liên kết hợp lệ]',
                 '    / lưu thêm liên kết nguồn cung',
                 'bỏSP(sp) [còn SP khác; được phép bỏ]',
                 '    / xóa liên kết được chọn',
                 'cậpNhật(tt) [hợp lệ] / lưu thông tin',
                 'xóaNCC() / từ chối: còn sản phẩm',
             ]),
             state('inactive', 90, 800, 430, 170, 'INACTIVE', 'Ngừng sử dụng', 'supplierState = INACTIVE', [
                 'entry / giữ bản ghi để lưu vết',
                 'Không dùng cho nghiệp vụ phát sinh mới',
             ]),
         ],
         final=(305, 1010),
         edges=[
             edge('create', 'initial', 'empty', [(305, 142), (305, 250)],
                  ['thêmNCC(tt)', '[QLY; thông tin hợp lệ]', '/ lưu nhà cung cấp mới'], (570, 175), 470),
             edge('first-product', 'empty', 'supplying', [(520, 345), (1120, 345)],
                  ['thêmSP(sp)', '[QLY; liên kết hợp lệ]', '/ lưu liên kết đầu tiên'], (820, 275), 550),
             edge('last-product', 'supplying', 'empty', [(1120, 520), (520, 520)],
                  ['bỏSP(sp)', '[QLY; SP cuối; được phép bỏ]', '/ xóa liên kết cuối cùng'], (820, 465), 550),
             edge('deactivate', 'empty', 'inactive', [(305, 550), (305, 800)],
                  ['xóaNCC()', '[QLY; đã xác nhận; chưa có phiếu nhập]', '/ vô hiệu hóa nhà cung cấp'], (600, 657), 550),
             edge('finish', 'inactive', 'final', [(305, 970), (305, 995)], [], (0, 0)),
         ],
         note=(770, 755, 830, 265),
         notes=[
             'Ký hiệu: sự kiện [điều kiện] / hành động.',
             'Thêm, sửa, xóa, thiết lập nguồn cung: QLY;',
             'tra cứu: NV hoặc QLY. Xử lý trong khung giữ trạng thái.',
             'Dữ liệu không hợp lệ / vi phạm ràng buộc: báo lỗi, giữ nguyên.',
             'Chỉ vô hiệu hóa khi không còn liên kết SP và chưa có phiếu nhập.',
             'SP dùng khi lập phiếu nhập phải thuộc nhà cung cấp đã chọn.',
             'Quy ước thiết kế: xóa logic; kết thúc vòng đời sử dụng,',
             'bản ghi vẫn được giữ. Không đặt luồng khôi phục chưa được quy định.',
         ],
         sources='Nguồn nghiệp vụ: UC-NCC, SEQ-NCC, ACT-NCC và SEQ-PN.',
         main=['empty', 'supplying'],
         types={'empty': 'start', 'supplying': 'active', 'inactive': 'neutral'}),
    dict(code='PLSP', name='Phân loại sản phẩm', size=(1680, 1080),
         subtitle='Đối tượng: một phân loại sản phẩm | Góc nhìn: tình trạng sử dụng của phân loại',
         initial=(305, 130),
         states=[
             state('unused', 90, 250, 430, 280, 'UNUSED', 'Chưa có sản phẩm', 'categoryState = UNUSED', [
                 'Số sản phẩm thuộc phân loại = 0',
                 'cậpNhật(tt) [hợp lệ] / lưu thông tin',
                 'traCứu(từKhóa) / trả thông tin phân loại',
             ]),
             state('in-use', 1120, 250, 470, 345, 'IN_USE', 'Có sản phẩm', 'categoryState = IN_USE', [
                 'Số sản phẩm thuộc phân loại > 0',
                 'gánSP(sp) [liên kết hợp lệ]',
                 '    / lưu thêm liên kết phân loại',
                 'bỏSP(sp) [còn SP khác; hợp lệ]',
                 '    / gỡ liên kết được chọn',
                 'cậpNhật(tt) [hợp lệ] / lưu thông tin',
                 'xóaPhânLoại() / từ chối: còn sản phẩm',
             ]),
             state('inactive', 90, 800, 430, 170, 'INACTIVE', 'Ngừng sử dụng', 'categoryState = INACTIVE', [
                 'entry / giữ bản ghi để lưu vết',
                 'Không gán cho sản phẩm mới',
             ]),
         ],
         final=(305, 1010),
         edges=[
             edge('create', 'initial', 'unused', [(305, 142), (305, 250)],
                  ['thêmPhânLoại(tt)', '[QLY; thông tin hợp lệ]', '/ lưu phân loại mới'], (570, 175), 470),
             edge('first-product', 'unused', 'in-use', [(520, 345), (1120, 345)],
                  ['gánSP(sp)', '[liên kết hợp lệ]', '/ gán sản phẩm đầu tiên'], (820, 275), 550),
             edge('last-product', 'in-use', 'unused', [(1120, 500), (520, 500)],
                  ['bỏSP(sp)', '[SP cuối; liên kết được gỡ hợp lệ]', '/ gỡ liên kết sản phẩm cuối cùng'], (820, 435), 550),
             edge('deactivate', 'unused', 'inactive', [(305, 530), (305, 800)],
                  ['xóaPhânLoại()', '[QLY; đã xác nhận; không có sản phẩm]', '/ vô hiệu hóa phân loại'], (600, 648), 550),
             edge('finish', 'inactive', 'final', [(305, 970), (305, 995)], [], (0, 0)),
         ],
         note=(770, 755, 830, 265),
         notes=[
             'Ký hiệu: sự kiện [điều kiện] / hành động.',
             'Thêm, sửa, xóa phân loại: QLY; tra cứu: NV hoặc QLY.',
             'Xử lý trong khung không làm đổi trạng thái.',
             'Dữ liệu không hợp lệ / vi phạm ràng buộc: báo lỗi, giữ nguyên.',
             'Gán hoặc bỏ sản phẩm là biến cố từ phân hệ Sản phẩm;',
             'thực hiện theo quyền và ràng buộc của phân hệ đó.',
             'Quy ước thiết kế: xóa logic; chỉ kết thúc vòng đời sử dụng,',
             'bản ghi vẫn được giữ. Không xóa khi còn sản phẩm liên kết.',
         ],
         sources='Nguồn nghiệp vụ: UC-PLSP, SEQ-PLSP, ACT-PLSP; thay đổi liên kết từ phân hệ Sản phẩm.',
         main=['unused', 'in-use'],
         types={'unused': 'start', 'in-use': 'active', 'inactive': 'neutral'}),
    dict(code='XT', name='Xác thực', size=(1680, 1320),
         subtitle='Đối tượng: ngữ cảnh xác thực của một người dùng hệ thống (NDHT) | Góc nhìn: tình trạng đăng nhập',
         initial=(170, 155),
         states=[
             state('logged-out', 90, 250, 430, 230, 'NOT_AUTHENTICATED', 'Chưa đăng nhập', 'authState = NOT_AUTHENTICATED', [
                 'entry / hiển thị màn hình đăng nhập',
                 'đăngNhập(tên, mk) [chưa nhập đủ]',
                 '    / báo lỗi; yêu cầu nhập lại',
             ]),
             state('checking', 1120, 250, 470, 230, 'AUTHENTICATING', 'Đang kiểm tra thông tin', 'authState = AUTHENTICATING', [
                 'do / tìm tài khoản đang hoạt động;',
                 '     kiểm tra mật khẩu',
                 'Chưa tạo phiên đăng nhập',
             ]),
             state('logged-in', 1120, 790, 470, 180, 'AUTHENTICATED', 'Đã đăng nhập', 'authState = AUTHENTICATED', [
                 'Phiên đã lưu thông tin tài khoản',
                 'do / duy trì phiên làm việc',
             ]),
             state('confirming', 90, 790, 430, 180, 'LOGOUT_CONFIRMATION', 'Chờ xác nhận đăng xuất', 'authState = LOGOUT_CONFIRMATION', [
                 'do / chờ lựa chọn xác nhận hoặc hủy',
                 'Phiên hiện tại vẫn còn hiệu lực',
             ]),
         ],
         edges=[
             edge('open', 'initial', 'logged-out', [(170, 167), (170, 250)],
                  ['khởi tạo ngữ cảnh', 'xác thực'], (290, 195), 230),
             edge('request', 'logged-out', 'checking', [(520, 350), (1120, 350)],
                  ['đăngNhập(tên, mk)', '[đã nhập đủ thông tin]', '/ gửi yêu cầu xác thực'], (820, 295), 550),
             edge('invalid', 'checking', 'logged-out', [(1355, 250), (1355, 150), (430, 150), (430, 250)],
                  ['[không có tài khoản hoạt động hoặc sai mật khẩu]', '/ báo lỗi; yêu cầu nhập lại'], (885, 112), 800),
             edge('valid', 'checking', 'logged-in', [(1355, 480), (1355, 790)],
                  ['[tài khoản hoạt động và mật khẩu đúng]', '/ tạo phiên; lưu tài khoản vào phiên;', 'mở trang chính'], (1050, 690), 580),
             edge('logout', 'logged-in', 'confirming', [(1120, 860), (520, 860)],
                  ['đăngXuất()', '/ hiển thị yêu cầu xác nhận'], (820, 820), 550),
             edge('confirm', 'confirming', 'logged-out', [(305, 790), (305, 480)],
                  ['đồngÝĐăngXuất()', '/ xóa phiên; đóng trang chính'], (600, 570), 550),
             edge('cancel', 'confirming', 'logged-in', [(305, 970), (305, 1050), (1355, 1050), (1355, 970)],
                  ['hủyĐăngXuất()', '/ giữ nguyên phiên; tiếp tục làm việc'], (820, 1010), 670),
         ],
         note=(60, 1120, 1560, 150),
         notes=[
             'Ký hiệu: sự kiện [điều kiện] / hành động. Nhánh không ghi sự kiện ở AUTHENTICATING là chuyển khi kiểm tra hoàn tất.',
             'Hai điều kiện xác thực loại trừ nhau: có tài khoản hoạt động + mật khẩu đúng, hoặc điều kiện đó không thỏa.',
             'Đăng xuất xóa phiên rồi trở về NOT_AUTHENTICATED; hủy đăng xuất giữ nguyên phiên.',
             'Không vẽ nút kết thúc: ngữ cảnh xác thực còn có thể đăng nhập lại; đăng xuất không xóa hoặc khóa tài khoản.',
         ],
         sources='Nguồn nghiệp vụ: UC-XT, SEQ đăng nhập, SEQ đăng xuất và ACT-XT.',
         main=['logged-out', 'checking', 'logged-in'],
         types={'logged-out': 'start', 'checking': 'active', 'logged-in': 'active', 'confirming': 'waiting'}),
]


def svg_text(x, y, text, size=16, color=INK, weight='normal', anchor='start', italic=False):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" style="white-space:pre" '
            f'font-weight="{weight}" text-anchor="{anchor}"'
            + (' font-style="italic"' if italic else '')
            + f'>{escape(text)}</text>')


def label_svg(e):
    if not e['label']:
        return ''
    x, y = e['at']
    w = e['width']
    return (f'<g data-edge-label="{e["id"]}">'
            f'<rect x="{x-w/2}" y="{y-17}" width="{w}" '
            f'height="{len(e["label"])*21+8}" rx="3" fill="white"/>'
            + ''.join(svg_text(x, y+i*21, t, 16, BLUE, anchor='middle') for i, t in enumerate(e['label']))
            + '</g>')


def make_drawio(d):
    w, h = d['size']
    mx = ET.Element('mxfile', host='app.diagrams.net', version='26.0.0')
    diagram = ET.SubElement(mx, 'diagram', id='state-'+d['code'], name=d['name'])
    model = ET.SubElement(diagram, 'mxGraphModel', dx=str(w), dy=str(h), grid='1', gridSize='10',
                          guides='1', tooltips='1', connect='1', arrows='1', fold='1', page='1',
                          pageScale='1', pageWidth=str(w), pageHeight=str(h), math='0', shadow='0')
    root = ET.SubElement(model, 'root')
    ET.SubElement(root, 'mxCell', id='0')
    ET.SubElement(root, 'mxCell', id='1', parent='0')

    def vertex(sid, value, x, y, bw, bh, style, parent='1'):
        c = ET.SubElement(root, 'mxCell', id=sid, value=value, style=style, vertex='1', parent=parent)
        ET.SubElement(c, 'mxGeometry', x=str(x), y=str(y), width=str(bw), height=str(bh), **{'as': 'geometry'})
        return c

    textstyle = 'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;overflow=hidden;fontFamily=Arial;spacing=0;'
    vertex('title', '<b>Sơ đồ trạng thái - '+d['name']+'</b>', 40, 20, w-80, 34, textstyle+'fontSize=27;')
    vertex('subtitle', d['subtitle'], 40, 62, w-80, 28, textstyle+'fontSize=16;fontColor=#666666;')
    for s in d['states']:
        x, y, sw, sh = (s[k] for k in ['x', 'y', 'w', 'h'])
        vertex(s['id'], '', x, y, sw, sh,
               'rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#222222;strokeWidth=2;')
        title = '<b>'+s['title']+'</b><br><i>'+s['description']+'</i>'
        vertex(s['id']+'-header', title, 12, 12, sw-24, 50,
               textstyle+'fontSize=17;align=center;', s['id'])
        vertex(s['id']+'-attribute', escape(s['attribute']), 14, 75, sw-28, 25,
               textstyle+'fontSize=15;fontColor=#666666;', s['id'])
        vertex(s['id']+'-actions', '<br>'.join(escape(t).replace('    ', '&nbsp;&nbsp;&nbsp;&nbsp;') for t in s['lines']),
               14, 112, sw-28, sh-122, textstyle+'fontSize=16;lineHeight=21;', s['id'])
        for num, sy in enumerate([65, 102]):
            c = ET.SubElement(root, 'mxCell', id=s['id']+f'-separator{num}',
                              style='endArrow=none;startArrow=none;strokeColor=#9a7979;strokeWidth=1;html=1;', edge='1', parent=s['id'])
            g = ET.SubElement(c, 'mxGeometry', relative='1', **{'as': 'geometry'})
            ET.SubElement(g, 'mxPoint', x='14', y=str(sy), **{'as': 'sourcePoint'})
            ET.SubElement(g, 'mxPoint', x=str(sw-14), y=str(sy), **{'as': 'targetPoint'})
    ix, iy = d['initial']
    vertex('initial', '', ix-11, iy-11, 22, 22, 'ellipse;html=1;fillColor=#222222;strokeColor=#222222;')
    if 'final' in d:
        fx, fy = d['final']
        vertex('final', '', fx-15, fy-15, 30, 30, 'ellipse;html=1;fillColor=#ffffff;strokeColor=#222222;strokeWidth=2;')
        vertex('final-dot', '', fx-9, fy-9, 18, 18, 'ellipse;html=1;fillColor=#222222;strokeColor=#222222;')
    states = {s['id']: s for s in d['states']}
    for e in d['edges']:
        start, end = e['points'][0], e['points'][-1]
        def port(sid, pt):
            if sid in states:
                s = states[sid]
                return ((pt[0]-s['x'])/s['w'], (pt[1]-s['y'])/s['h'])
            return (0.5, 1 if sid == 'initial' else 0)
        ex, ey = port(e['source'], start)
        tx, ty = port(e['target'], end)
        c = ET.SubElement(root, 'mxCell', id=e['id'], edge='1', parent='1', source=e['source'], target=e['target'],
                          style=f'edgeStyle=none;rounded=1;endArrow=open;endFill=0;strokeColor=#333333;strokeWidth=1.5;exitX={ex};exitY={ey};exitPerimeter=0;entryX={tx};entryY={ty};entryPerimeter=0;')
        g = ET.SubElement(c, 'mxGeometry', relative='1', **{'as': 'geometry'})
        if len(e['points']) > 2:
            arr = ET.SubElement(g, 'Array', **{'as': 'points'})
            for px, py in e['points'][1:-1]:
                ET.SubElement(arr, 'mxPoint', x=str(px), y=str(py))
        if e['label']:
            lx, ly = e['at']
            vertex(e['id']+'-label', '<br>'.join(escape(t) for t in e['label']), lx-e['width']/2, ly-17,
                   e['width'], len(e['label'])*21+8,
                   textstyle+'fontSize=16;fontColor=#303f92;align=center;fillColor=#ffffff;')
    nx, ny, nw, nh = d['note']
    vertex('notes', '<b>Ghi chú</b><br>'+'<br>'.join('• '+escape(t) for t in d['notes']), nx, ny, nw, nh,
           'shape=note;size=15;html=1;whiteSpace=wrap;fillColor=#ffffff;strokeColor=#777777;fontFamily=Arial;fontSize=16;align=left;verticalAlign=top;spacing=14;')
    vertex('source', escape(d['sources'])+'<br>Quy tắc ký pháp: Chương 5, trang 44-49, 52-54. Tên thuộc tính trạng thái là đề xuất phân tích.',
           40, h-38, w-80, 34, textstyle+'fontSize=12;fontColor=#777777;')
    return ET.tostring(mx, encoding='unicode')


def make_svg(d, drawio):
    w, h = d['size']
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
             f'content="{escape(drawio, quote=True)}" role="img" aria-labelledby="title desc">',
             f'<title id="title">Sơ đồ trạng thái - {escape(d["name"])}</title>',
             '<desc id="desc">Sơ đồ UML theo Chương 5. Có thể mở và chỉnh sửa bằng diagrams.net.</desc>',
             '<defs><marker id="arrow" markerWidth="12" markerHeight="10" refX="10" refY="5" orient="auto" markerUnits="userSpaceOnUse">'
             '<path d="M 1 1 L 10 5 L 1 9" fill="none" stroke="#333333" stroke-width="1.5"/></marker></defs>',
             '<rect width="100%" height="100%" fill="white"/>', '<g font-family="Arial, sans-serif">',
             svg_text(40, 45, 'Sơ đồ trạng thái - '+d['name'], 27, weight='bold'),
             svg_text(40, 78, d['subtitle'], 16, '#666666')]
    for e in d['edges']:
        points = ' '.join(f'{x},{y}' for x, y in e['points'])
        parts.append(f'<polyline data-edge="{e["id"]}" points="{points}" fill="none" stroke="#333333" stroke-width="1.6" stroke-linejoin="round" marker-end="url(#arrow)"/>')
    ix, iy = d['initial']
    parts.append(f'<circle data-initial="true" cx="{ix}" cy="{iy}" r="11" fill="{INK}"/>')
    if 'final' in d:
        fx, fy = d['final']
        parts.append(f'<g data-final="true"><circle cx="{fx}" cy="{fy}" r="15" fill="white" stroke="{INK}" stroke-width="1.8"/>'
                     f'<circle cx="{fx}" cy="{fy}" r="9" fill="{INK}"/></g>')
    for s in d['states']:
        x, y, sw, sh = (s[k] for k in ['x', 'y', 'w', 'h'])
        parts.append(f'<g data-state="{s["id"]}"><rect x="{x}" y="{y}" width="{sw}" height="{sh}" rx="15" fill="white" stroke="{INK}" stroke-width="1.8"/>')
        parts.append(svg_text(x+sw/2, y+27, s['title'], 18, weight='bold', anchor='middle'))
        parts.append(svg_text(x+sw/2, y+50, s['description'], 16, anchor='middle', italic=True))
        for sy in [65, 102]:
            parts.append(f'<line x1="{x+14}" y1="{y+sy}" x2="{x+sw-14}" y2="{y+sy}" stroke="#9a7979" stroke-width="1"/>')
        parts.append(svg_text(x+14, y+89, s['attribute'], 15, '#666666'))
        parts.extend(svg_text(x+14, y+131+i*22, line) for i, line in enumerate(s['lines']))
        parts.append('</g>')
    parts.extend(label_svg(e) for e in d['edges'])
    x, y, nw, nh = d['note']
    parts.append(f'<g data-note="true"><path d="M{x},{y} H{x+nw-15} L{x+nw},{y+15} V{y+nh} H{x} Z M{x+nw-15},{y} V{y+15} H{x+nw}" fill="white" stroke="#777777" stroke-width="1"/>')
    parts.append(svg_text(x+14, y+27, 'Ghi chú', 17, weight='bold'))
    parts.extend(svg_text(x+14, y+53+i*24, '• '+t, 16) for i, t in enumerate(d['notes']))
    parts.append('</g>')
    parts.append(svg_text(40, h-23, d['sources'], 12, '#777777'))
    parts.append(svg_text(40, h-7, 'Quy tắc ký pháp: Chương 5, trang 44-49, 52-54. Tên thuộc tính trạng thái là đề xuất phân tích.', 12, '#777777'))
    parts.append('</g></svg>')
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ''.join(parts)


def make_candidate(d):
    transitions = []
    for e in d['edges']:
        if e['source'] in ('initial', 'final') or e['target'] == 'final':
            continue
        text = e['label']
        transitions.append(dict(id=e['id'], **{'from': e['source'], 'to': e['target']},
                                label=text[0], note=' '.join(text[1:])))
    if d['code'] == 'KH':
        transitions.append(dict(id='update-saved', **{'from': 'saved', 'to': 'saved'},
                                label='cậpNhật(tt)', note='[hợp lệ] / lưu thông tin'))
    return dict(schema_version=3, diagram_type='lifecycle',
                meta=dict(title='Sơ đồ trạng thái - '+d['name'], locale='vi',
                          output=f'4.New_State/Tuong_tac/{d["code"]}.html', quality_profile='showcase'),
                mainPath=d['main'],
                states=[dict(id=s['id'], type=d['types'][s['id']], label=s['title'],
                             sublabel=s['description'], icon='none') for s in d['states']],
                transitions=transitions,
                cards=[dict(dot='slate', title=s['title']+' - Xử lý trong trạng thái',
                            items=[s['attribute'], *[line.strip() for line in s['lines']]]) for s in d['states']]
                      + [dict(dot='slate', title='Khởi tạo', items=d['edges'][0]['label']),
                         dict(dot='slate', title='Quy ước và phạm vi', items=d['notes'])])


def main():
    for folder in ['PNG', 'Nguon_drawio', 'Tuong_tac']:
        (ROOT / folder).mkdir(exist_ok=True)
    for d in DIAGRAMS:
        assert len({s['id'] for s in d['states']}) == len(d['states'])
        ids = {s['id'] for s in d['states']} | {'initial', 'final'}
        assert all(e['source'] in ids and e['target'] in ids for e in d['edges'])
        assert sum(e['source'] == 'initial' for e in d['edges']) == 1
        assert all(s['h'] >= 140 + (len(s['lines'])-1)*22 for s in d['states'])
        drawio = make_drawio(d)
        svg = make_svg(d, drawio)
        ET.fromstring(drawio)
        parsed = ET.fromstring(svg)
        assert parsed.attrib['content'] == drawio
        (ROOT / 'Nguon_drawio' / f'{d["code"]}.drawio').write_text(drawio, encoding='utf-8')
        (ROOT / f'{d["code"]}.drawio.svg').write_text(svg, encoding='utf-8')
        (ROOT / '.source' / f'{d["code"]}.lifecycle.json').write_text(json.dumps(make_candidate(d), ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'{d["code"]}: {len(d["states"])} trạng thái, {len(d["edges"])} đường chuyển; XML/SVG hợp lệ')
    (ROOT / '.source' / 'diagrams.json').write_text(json.dumps(DIAGRAMS, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
