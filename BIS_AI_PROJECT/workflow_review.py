"""Local evidence review. Never calls a shop API or grants publishing approval."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from product_quality import fingerprint, validate_product, match_product
from safe_publish import source_text


def review_product(root, product):
    root = Path(root).resolve()
    checks = []
    def add(key, label, state, detail):
        checks.append(dict(key=key, label=label, state=state, detail=detail))
    try:
        text = source_text(root, product)
    except Exception:
        text = None
    validation = validate_product(product, text)
    add('technical', 'Nguồn và nội dung', 'PASS' if validation['passed'] else 'BLOCKED',
        'Cấu trúc và trích dẫn khớp; vẫn cần người duyệt tính đúng.' if validation['passed'] else '; '.join(validation['errors']))
    meta = str(product.get('meta_description') or '')
    add('marketing', 'SEO', 'PASS' if 140 <= len(meta) <= 160 else 'BLOCKED',
        f'{len(meta)} ký tự; mục tiêu nội bộ 140–160. Không cam kết thứ hạng tìm kiếm.')
    try:
        manifest = json.loads((root/'Google_Drive_Storage'/'image_review_manifest.json').read_text(encoding='utf-8'))
        item = manifest[str(product['sku'])]
        path = Path(item['final_image'])
        path = (root/path).resolve()
        if not path.is_relative_to(root/'Google_Drive_Storage'):
            raise ValueError('Image outside storage')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        from PIL import Image
        with Image.open(path) as image:
            valid = image.size == (1254, 1254)
        valid = valid and item.get('status') == 'APPROVED' and item.get('approved_sha256') == digest
        if not valid:
            raise ValueError('Image changed or not approved')
        add('images', 'Ảnh thành phẩm', 'PASS', 'Ảnh 1254×1254 có hash khớp phiên bản đã duyệt.')
    except Exception:
        add('images', 'Ảnh thành phẩm', 'BLOCKED', 'Thiếu ảnh đã duyệt, sai kích thước hoặc ảnh đã thay đổi.')
    try:
        items = json.loads((root/'bistextile_existing_products.json').read_text(encoding='utf-8'))
        if not isinstance(items, list) or not items:
            raise ValueError('Missing snapshot')
        duplicate = match_product(product, items)
        add('operations', 'Đối soát bản lưu', 'REVIEW', duplicate['reason'] + ' — đây là bản lưu, cần quét live trước khi đăng.')
    except Exception:
        add('operations', 'Đối soát bản lưu', 'UNKNOWN', 'Chưa có bản lưu hợp lệ; không kết luận sản phẩm mới.')
    approved = product.get('status') == 'APPROVED' and product.get('_review_hash') == fingerprint({k:v for k,v in product.items() if not k.startswith('_')})
    add('approval', 'Duyệt nội dung', 'PASS' if approved else 'REVIEW',
        'Hash nội dung khớp bản duyệt.' if approved else 'Cần duyệt đúng phiên bản hiện hành.')
    add('memory', 'Đồng bộ bền vững', 'UNKNOWN', 'Kiểm tra tại Memory; kết quả local không xác nhận đồng bộ Google.')
    return dict(sku=product.get('sku'), revision=fingerprint(product),
                checked_at=datetime.now(timezone.utc).isoformat(), state='NEEDS_REVIEW',
                checks=checks, publish_allowed=False,
                detail='Kiểm tra cục bộ; không duyệt sản phẩm, không quét live và không đăng Haravan.')
