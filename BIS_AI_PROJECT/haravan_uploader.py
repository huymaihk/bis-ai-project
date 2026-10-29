"""
BIS Textile Pipeline - Haravan Uploader
SAFETY: Will NOT run unless HARAVAN_PUSH_ENABLED = True AND products have status APPROVED.
"""
import requests
import json
import time
from datetime import datetime

from config import (
    HARAVAN_TOKEN,
    HARAVAN_SHOP,
    HARAVAN_PUSH_ENABLED,
    STATUS_APPROVED,
    STATUS_PUSHED,
)

HARAVAN_API_BASE = "https://app.haravan.com/api/v1"


def _haravan_headers() -> dict:
    return {
        "Authorization": f"Bearer {HARAVAN_TOKEN}",
        "Content-Type": "application/json",
        "X-Haravan-Shop": HARAVAN_SHOP,
    }


def build_7_block_html(product: dict) -> str:
    """Build the official 7-block product description HTML according to BIS Textile spec."""
    title_vi = product.get("product_name") or ""
    title_en = product.get("product_name_en") or ""
    sku      = product.get("sku") or ""
    desc     = product.get("description") or ""
    vendor   = product.get("vendor") or "AATCC"
    origin   = product.get("brand_origin") or "Hoa Kỳ (USA)"
    role     = product.get("publisher_role") or "Nhà xuất bản tiêu chuẩn quốc tế"

    # Block 1 & 2: Titles
    html = f"""<div class="bis-product-description" style="font-family: Arial, Helvetica, sans-serif; line-height: 1.6; color: #1e293b;">
  <h1 style="font-size: 18px; font-weight: bold; color: #1e293b; margin-bottom: 4px;">{title_vi}</h1>
  <h2 style="font-size: 16px; font-weight: bold; color: #475569; margin-top: 0; margin-bottom: 10px;">{title_en}</h2>
  
  <div style="font-size: 13px; color: #334155; padding: 6px 12px; background: #f8fafc; border-radius: 6px; margin-bottom: 12px; border: 1px solid #e2e8f0;">
    <strong>Hãng ban hành:</strong> {vendor} &bull; <strong>Quốc gia:</strong> {origin} &bull; <strong>Vai trò:</strong> {role}
  </div>

  <div style="font-size: 13px; color: #1e293b; margin-bottom: 14px; text-align: justify;">
    <p>{desc}</p>
  </div>

  <div style="margin-bottom: 14px;">
    <div style="font-weight: bold; font-size: 14px; margin-bottom: 6px; color: #0f172a;">Đặc điểm nổi bật:</div>
    <ul style="padding-left: 20px; margin: 0; list-style-type: disc; color: #334155; font-size: 13px;">
      <li style="margin-bottom: 4px;">Tài liệu và tiêu chuẩn chính hãng do {vendor} ban hành.</li>
      <li style="margin-bottom: 4px;">Phương pháp thử nghiệm được chuẩn hóa áp dụng toàn cầu trong phòng lab dệt may.</li>
      <li style="margin-bottom: 4px;">Đáp ứng đầy đủ yêu cầu kiểm nghiệm chất lượng theo chuỗi cung ứng quốc tế.</li>
    </ul>
  </div>

  <div style="margin-bottom: 16px;">
    <div style="font-weight: bold; font-size: 14px; margin-bottom: 6px; color: #0f172a;">Thông số kỹ thuật chính:</div>
    <table style="width: 100%; border-collapse: collapse; margin-top: 6px;">
      <tbody>
        <tr><td style="width: 39%; background: #f8fafc; font-weight: 600; border: 1px solid #e2e8f0; padding: 8px 12px; font-size: 13px;">Mã sản phẩm (SKU)</td><td style="border: 1px solid #e2e8f0; padding: 8px 12px; font-size: 13px;">{sku}</td></tr>
        <tr><td style="width: 39%; background: #f8fafc; font-weight: 600; border: 1px solid #e2e8f0; padding: 8px 12px; font-size: 13px;">Tổ chức ban hành</td><td style="border: 1px solid #e2e8f0; padding: 8px 12px; font-size: 13px;">{vendor}</td></tr>
        <tr><td style="width: 39%; background: #f8fafc; font-weight: 600; border: 1px solid #e2e8f0; padding: 8px 12px; font-size: 13px;">Phạm vi chuyên ngành</td><td style="border: 1px solid #e2e8f0; padding: 8px 12px; font-size: 13px;">Kiểm nghiệm và đánh giá chất lượng dệt may</td></tr>
        <tr><td style="width: 39%; background: #f8fafc; font-weight: 600; border: 1px solid #e2e8f0; padding: 8px 12px; font-size: 13px;">Đơn vị phân phối</td><td style="border: 1px solid #e2e8f0; padding: 8px 12px; font-size: 13px;">BIS Textile Việt Nam (bistextile.com)</td></tr>
      </tbody>
    </table>
  </div>

  <!-- KHỐI 7: Tài liệu & Sản phẩm liên quan (Hiển thị tên đầy đủ, nhấp mở trang thật) -->
  <div style="margin-top: 18px; padding-top: 14px; border-top: 1px dashed #cbd5e1;">
    <div style="font-weight: bold; font-size: 13px; color: #0f172a; margin-bottom: 8px;">Tài liệu & Tiêu chuẩn liên quan:</div>
    <div style="display: flex; flex-direction: column; gap: 8px;">
      <a href="https://bistextile.com/products/sach-textile-coloration-for-the-retail-supply-chain-09616a" target="_blank" rel="noopener noreferrer" style="display: inline-flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: #f0f9ff; color: #0369a1; border: 1px solid #bae6fd; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 500;">
        <span>📄 Sách nhuộm màu hàng dệt may cho chuỗi cung ứng bán lẻ AATCC 09616A</span>
        <span style="font-size: 11px; color: #0284c7; background: #fff; padding: 2px 6px; border-radius: 4px; border: 1px solid #e0f2fe;">Mở trang ↗</span>
      </a>
      <a href="https://bistextile.com/search?q=AATCC" target="_blank" rel="noopener noreferrer" style="display: inline-flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: #f0f9ff; color: #0369a1; border: 1px solid #bae6fd; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 500;">
        <span>📄 Danh mục đầy đủ tài liệu & vật tư kiểm nghiệm tiêu chuẩn AATCC tại BIS Textile</span>
        <span style="font-size: 11px; color: #0284c7; background: #fff; padding: 2px 6px; border-radius: 4px; border: 1px solid #e0f2fe;">Mở trang ↗</span>
      </a>
    </div>
  </div>
</div>"""
    return html


def _product_to_haravan_payload(product: dict) -> dict:
    """Convert BIS product record to Haravan product payload."""
    title = product.get("product_name") or product.get("product_name_en") or "Unnamed Product"
    body_html = build_7_block_html(product)
    
    payload = {
        "product": {
            "title": title,
            "body_html": body_html,
            "vendor": "BIS Textile",
            "product_type": product.get("category", "Vải"),
            "tags": ",".join(filter(None, [
                product.get("category"),
                product.get("material"),
                product.get("color"),
                product.get("pattern"),
            ])),
            "variants": [
                {
                    "sku": product.get("sku") or "",
                    "price": product.get("price_vnd") or "0",
                    "inventory_quantity": 9999,
                    "fulfillment_service": "manual",
                }
            ],
            "metafields": [
                {"namespace": "bis_textile", "key": "extracted_id",    "value": product.get("product_id", ""), "type": "single_line_text_field"},
                {"namespace": "bis_textile", "key": "material",        "value": product.get("material", ""),   "type": "single_line_text_field"},
                {"namespace": "bis_textile", "key": "width_cm",        "value": str(product.get("width_cm") or ""), "type": "single_line_text_field"},
                {"namespace": "bis_textile", "key": "weight_gsm",      "value": str(product.get("weight_gsm") or ""), "type": "single_line_text_field"},
                {"namespace": "bis_textile", "key": "min_order_qty",   "value": str(product.get("min_order_qty") or ""), "type": "single_line_text_field"},
            ],
        }
    }
    return payload


def push_to_haravan(products: list[dict]) -> list[dict]:
    """
    Push APPROVED products to Haravan.
    
    SAFETY CHECKS:
    1. HARAVAN_PUSH_ENABLED must be True in config.py
    2. Each product must have status == APPROVED
    
    Returns list of results with haravan_product_id filled in.
    """
    # ── SAFETY GATE ──────────────────────────────────────────────────────────
    if not HARAVAN_PUSH_ENABLED:
        raise RuntimeError(
            "🚫 HARAVAN PUSH BLOCKED: HARAVAN_PUSH_ENABLED = False in config.py\n"
            "Set HARAVAN_PUSH_ENABLED = True only after manual product review in Google Sheets."
        )

    approved = [p for p in products if p.get("status") == STATUS_APPROVED]
    if not approved:
        print("⚠ No APPROVED products found — nothing to push.")
        return []

    print(f"\n🚀 Pushing {len(approved)} APPROVED products to Haravan …")
    results = []
    
    for i, product in enumerate(approved):
        try:
            payload = _product_to_haravan_payload(product)
            resp = requests.post(
                f"{HARAVAN_API_BASE}/products.json",
                headers=_haravan_headers(),
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            
            haravan_id = resp.json()["product"]["id"]
            product["haravan_product_id"] = haravan_id
            product["status"] = STATUS_PUSHED
            product["updated_at"] = datetime.utcnow().isoformat() + "Z"
            
            print(f"  [{i+1}/{len(approved)}] ✓ Pushed: {product.get('product_name')} → Haravan ID {haravan_id}")
            results.append({"success": True, "product": product, "haravan_id": haravan_id})
            
            # Rate limit: 2 requests/second
            time.sleep(0.5)
            
        except requests.HTTPError as e:
            print(f"  [{i+1}/{len(approved)}] ✗ HTTP Error: {e.response.status_code} — {e.response.text[:200]}")
            results.append({"success": False, "product": product, "error": str(e)})
        except Exception as e:
            print(f"  [{i+1}/{len(approved)}] ✗ Error: {e}")
            results.append({"success": False, "product": product, "error": str(e)})
    
    pushed = sum(1 for r in results if r["success"])
    print(f"\n✅ Haravan push complete: {pushed}/{len(approved)} succeeded")
    return results

