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
        'MANUAL' not in str(result.get('product_name_en','')).upper() or
        len(result.get('description',''))>450):
        return result
    result['description']=(
        'AATCC Manual of International Test Methods and Procedures là sổ tay tổng hợp các phương pháp thử, quy trình phòng thí nghiệm, quy trình đánh giá và chuyên khảo do các Ủy ban Nghiên cứu của AATCC xây dựng. Mã 03026A là phiên bản sách bìa cứng được giới thiệu trong catalogue.\n\n'
        'Tài liệu được cập nhật và xuất bản hằng năm. Theo catalogue, ấn phẩm năm 2026 đánh dấu lần xuất bản thứ 100. Khi lựa chọn tài liệu cho công việc, cần đối chiếu năm xuất bản và phiên bản phương pháp với yêu cầu đang áp dụng; thông tin về ấn bản 2026 không phải xác nhận tồn kho hiện tại.\n\n'
        'Trang nguồn giới thiệu phạm vi các phương pháp và quy trình AATCC gồm độ bền màu, nhuộm và xử lý ướt, nhận diện và phân tích, giặt và giặt khô, quản lý độ ẩm, khả năng chống nước và tác động thời tiết, cùng các chủ đề về tính bền vững, đặc tính sinh học và thử nghiệm thảm. Đây là thông tin về phạm vi tài liệu, không phải cam kết mọi phép thử phù hợp với mọi sản phẩm.\n\n'
        'Catalogue cũng phân biệt sách bìa cứng 03026A với bản tải PDF 03026B. Các phương pháp và chuyên khảo riêng lẻ được giới thiệu ở mục khác. Trước khi sử dụng một phương pháp, người đọc cần tra cứu nội dung đầy đủ trong đúng tài liệu và phiên bản được yêu cầu.')
    result['highlights']=[
        'Tập hợp phương pháp thử, quy trình phòng thí nghiệm, quy trình đánh giá và chuyên khảo của AATCC.',
        'Mã 03026A: sách bìa cứng; bản tải PDF có mã riêng 03026B.',
        'Cập nhật và xuất bản hằng năm; catalogue ghi ấn phẩm năm 2026 là lần xuất bản thứ 100.',
        'Phạm vi tài liệu được giới thiệu gồm độ bền màu, xử lý ướt, phân tích và chăm sóc sản phẩm dệt may.']
    return result
