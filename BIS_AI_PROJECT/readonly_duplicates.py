"""Read-only duplicate evidence. No product/draft mutations or publishing authority."""
import time
from datetime import datetime, timezone
import requests
from product_quality import match_product

WEB_URL = 'https://bistextile.com/collections/all/products.json'


def scan_website(session=requests, pause=time.sleep):
    items, seen = [], set()
    for page in range(1, 1001):
        response = session.get(WEB_URL, params={'page': page, 'limit': 50}, timeout=20)
        response.raise_for_status()
        data = response.json()
        rows = data.get('products') if isinstance(data, dict) else None
        if not isinstance(rows, list) or any(not isinstance(row, dict) or not row.get('id') for row in rows):
            raise ValueError('Invalid public catalogue response')
        ids = [str(row['id']) for row in rows]
        if len(set(ids)) != len(ids) or seen.intersection(ids):
            raise ValueError('Public pagination repeated products')
        seen.update(ids)
        items.extend(rows)
        if len(rows) < 50:
            return items
        pause(0.25)
    raise ValueError('Public pagination incomplete')


def check_sources(product, headers):
    from safe_publish import scan_store
    reports = []
    for label, scan in [('Haravan API', lambda: scan_store(headers)), ('bistextile.com', scan_website)]:
        report = {'source': label, 'checked_at': datetime.now(timezone.utc).isoformat()}
        try:
            rows = scan()
            if not isinstance(rows, list):
                raise ValueError('Invalid products list')
            report.update(match_product(product, rows), complete=True, count=len(rows))
        except Exception:
            report.update(state='UNVERIFIED', complete=False, count=0,
                          reason='Chưa đọc đủ nguồn; kiểm tra kết nối/quyền đọc. Không kết luận chưa trùng.')
        reports.append(report)
    # Positive evidence still blocks creation when another source fails.
    chosen = next((r for r in reports if r['state'] == 'MATCH'), None)
    chosen = chosen or next((r for r in reports if r['state'] == 'REVIEW'), None)
    incomplete = any(not r['complete'] for r in reports)
    state = chosen['state'] if chosen else ('UNVERIFIED' if incomplete else 'NO_MATCH')
    return dict(state=state, reason=chosen['reason'] if chosen else (
        'Chưa kiểm tra đủ hai nguồn; chưa được coi là sản phẩm mới.' if incomplete else
        'Chưa thấy trùng trong hai nguồn vừa đọc; kết quả không cấp quyền đăng sản phẩm.'),
        url=chosen.get('url', '') if chosen else '', id=chosen.get('id') if chosen else None,
        blocked=state != 'NO_MATCH' or incomplete, complete=not incomplete, sources=reports,
        source='Haravan + bistextile.com (chỉ đọc)', checked_at=datetime.now(timezone.utc).isoformat(),
        count=sum(r['count'] for r in reports))
