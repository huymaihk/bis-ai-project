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
        info.update(suggested_name=saved['name'], reason='Tên đã lưu từ hiệu chỉnh của người dùng.')
        if saved['sha256']==row.get('_source_sha256'):
            info['state']='NAME_APPROVED'
    elif len(heads)>1:
        info['reason']='Có hiệu chỉnh xung đột; cần đối chiếu trước khi lưu.'
    if not info['suggested_name']:
        from catalog_master_data import CATALOG_MASTER
        reference=CATALOG_MASTER.get(str(row.get('sku','')), {})
        normalize=lambda s: re.sub(r'\W+',' ',str(s).casefold()).strip()
        if reference and normalize(reference.get('en'))==normalize(row.get('product_name_en')):
            info.update(suggested_name=reference.get('vi',''),reason='Gợi ý từ tên tham chiếu cùng SKU và tên tiếng Anh; chưa được duyệt.')
    return info
