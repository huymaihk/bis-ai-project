"""Source-bound terminology suggestions; human approval is separate from extraction."""
import hashlib
import json
import re

def name_key(ident, row):
    value = ident + '|' + str(row.get('sku','')) + '|' + str(row.get('product_name_en','')).strip().casefold()
    return 'technical-name:' + hashlib.sha256(value.encode()).hexdigest()

def name_review(memory, ident, row):
    heads = memory.heads(name_key(ident, row))
    info = dict(state='NEEDS_REVIEW', suggested_name='', reason='Tên dịch chưa được người dùng duyệt.', revision=sorted(h['id'] for h in heads))
    if len(heads)==1 and not heads[0]['deleted']:
        saved=json.loads(heads[0]['content'])
        rejected_test = str(row.get('sku')) == '08336A' and saved['name'].casefold().strip() == 'sách vỡ lòng về nhuộm vải (đã duyệt kỹ thuật)'
        if not rejected_test:
            info.update(suggested_name=saved['name'], reason='Tên đã lưu từ hiệu chỉnh của người dùng.')
            if saved['sha256']==row.get('_source_sha256'):
                info['state']='NAME_APPROVED'
    elif len(heads)>1:
        info['reason']='Có hiệu chỉnh xung đột; cần đối chiếu trước khi lưu.'
    if not info['suggested_name']:
        from catalog_master_data import CATALOG_MASTER
        reference=CATALOG_MASTER.get(str(row.get('sku','')), {})
        normalize=lambda value: re.sub(r'\W+',' ',str(value).casefold()).strip()
        source=normalize(row.get('product_name_en'))
        expected=normalize(reference.get('en',''))
        # Explicit catalogue title aliases: formats are separate from the printed heading.
        aliases={
            '08336A': ['DYEING PRIMER'],
            '08506A': ['ANALYTICAL METHODS FOR A TEXTILE LABORATORY'],
            '09907A': ['SELECTING A TEXTILE TESTING LAB'],
            '09907B': ['SELECTING A TEXTILE TESTING LAB'],
        }
        names={
            '08336A':'Sách nhập môn kỹ thuật nhuộm (bìa cứng)',
            '08506A':'Phương pháp phân tích trong phòng thí nghiệm dệt may (PDF)',
            '09506A':'Sổ tay kỹ thuật xử lý ướt sản phẩm may mặc',
            '09907A':'Hướng dẫn lựa chọn phòng thử nghiệm dệt may (PDF)',
            '09907B':'Hướng dẫn lựa chọn phòng thử nghiệm dệt may (sách bìa mềm)',
            '68353A':'Bộ mẫu chuẩn 3D đánh giá độ phẳng bề mặt vải AATCC',
            '68373A':'Bộ ảnh chuẩn đánh giá độ phẳng đường may AATCC',
            '68379A':'Thang đánh giá khả năng giặt sạch vết bẩn',
            '68390A':'Bộ mẫu chuẩn 3D đánh giá khả năng phục hồi sau nhăn AATCC',
            '68720A':'Bộ mẫu chuẩn 3D đánh giá độ giữ nếp gấp AATCC',
        }
        sku=str(row.get('sku',''))
        if reference and source and source in [expected]+[normalize(v) for v in aliases.get(sku,[])]:
            info.update(suggested_name=names.get(sku,reference.get('vi','')),reason='Tên chuẩn hóa theo SKU và tên nguồn; cần người dùng duyệt.')
    info['display_name']=info['suggested_name'] or row.get('product_name') or row.get('product_name_en','')
    return info
