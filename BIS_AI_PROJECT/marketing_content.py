"""Owner's customer-facing copy policy; evidence/history are never rewritten."""
import re

FORBIDDEN_SENTENCE='Chứng nhận xuất xứ và chất lượng rõ ràng, cung cấp đầy đủ chứng từ CO/CQ từ BIS Textile.'

def clean_text(value):
    text=re.sub(r'\[\s*Đã kiểm tra\s*\]', '', str(value or ''),flags=re.I)
    text=text.replace(FORBIDDEN_SENTENCE,'')
    # Commercial certificate promises are not product specifications.
    text=re.sub(r'[^.!?\n]*CO\s*/\s*CQ[^.!?\n]*(?:[.!?]|$)', '', text,flags=re.I)
    return text.strip()

def clean_product(product):
    result=dict(product)
    for key in ('product_name','description','meta_description','meta_title'):
        if key in result:
            result[key]=clean_text(result[key])
    if 'highlights' in result:
        values=result['highlights'] or []
        if isinstance(values,str): values=values.splitlines()
        result['highlights']=[clean_text(v) for v in values if clean_text(v)]
    return result

def expand_manual(product, source):
    result=clean_product(product)
    source=str(source or '')
    if (result.get('sku')!='03026A' or '03026A' not in source or
        '100th Edition' not in source or 'Research Committees' not in source or
        'MANUAL' not in str(result.get('product_name_en','')).upper()):
        return result
    result['description']='Sổ tay AATCC Manual of International Test Methods and Procedures tập hợp các phương pháp thử, quy trình phòng thí nghiệm, quy trình đánh giá và chuyên khảo do các Ủy ban Nghiên cứu AATCC xây dựng. Tài liệu phục vụ tra cứu phương pháp đánh giá sản phẩm dệt may, bao gồm độ bền màu, xử lý ướt, phân tích và chăm sóc vật liệu.'
    result['highlights']=[
        'Mã 03026A là sách bìa cứng; bản tải PDF có mã riêng 03026B.',
        'Cập nhật hằng năm; catalogue ghi ấn phẩm năm 2026 là lần xuất bản thứ 100.']
    return result


def concise_suggestion(product):
    description=clean_text(product.get('description',''))
    sentences=re.split(r'(?<=[.!?])\s+|\n+',description)
    selected=[]
    for sentence in sentences:
        if len(' '.join(selected+[sentence]))>450: break
        selected.append(sentence)
    short=' '.join(selected).strip()
    if not short and description:
        short=description[:447].rsplit(' ',1)[0]+'…'
    highlights=[]
    words=set(re.findall(r'\w+',short.casefold()))
    for item in product.get('highlights') or []:
        text=clean_text(item)
        tokens=set(re.findall(r'\w+',text.casefold()))
        if text and text not in short and len(tokens & words)/max(1,len(tokens))<0.75 and text not in highlights:
            highlights.append(text)
    return {'description':short,'highlights':highlights[:4],'needs_review':True}
