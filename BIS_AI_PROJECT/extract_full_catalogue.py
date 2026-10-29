"""
BIS Textile - Full Catalogue Extraction Script (Pages 11 to 28)
Extracts all 90+ products across testing materials, equipment, and consumables.
Syncs results to extracted_products_cache.json and Google Sheets.
"""
import sys
import os
import json
import time
from pathlib import Path
import pymupdf

PROJECT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_DIR))

from agent_technical import AgentTechnical
from agent_operations import AgentOperations
from sheets_manager import append_products

def run_full_scan():
    pdf_path = PROJECT_DIR / "catalogue_sample.pdf"
    cache_path = PROJECT_DIR / "extracted_products_cache.json"

    # Load existing cache
    existing_products = []
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                existing_products = json.load(f)
        except Exception:
            existing_products = []

    existing_skus = {p.get("sku") for p in existing_products if p.get("sku")}
    print(f"📦 Đang có {len(existing_products)} sản phẩm trong bộ nhớ cache.")

    tech = AgentTechnical(PROJECT_DIR)
    ops = AgentOperations(PROJECT_DIR)

    # Kết nối Google Sheets
    ws = None
    try:
        ss, ws = ops.connect_sheets()
        print(f"📊 Đã kết nối Google Sheets: {ss.url}")
    except Exception as e:
        print(f"⚠ Không thể kết nối Sheets trực tiếp: {e}")

    doc = pymupdf.open(str(pdf_path))
    total_pages = len(doc)
    print(f"📄 Cuốn catalogue có tổng cộng {total_pages} trang.")

    # Các trang chứa sản phẩm dệt may & thiết bị: từ trang 11 đến trang 28
    pages_to_scan = list(range(11, 29))
    print(f"🚀 Bắt đầu quét chuyên sâu các trang sản phẩm: {pages_to_scan[0]} đến {pages_to_scan[-1]}...")

    newly_added = 0
    for p_num in pages_to_scan:
        p_idx = p_num - 1
        page = doc[p_idx]
        text_len = len(page.get_text().strip())
        
        # Bỏ qua các trang quá ít chữ hoặc trang phân mục trống
        if text_len < 50:
            print(f"  ⏭ Bỏ qua trang {p_num} (Trang tiêu đề/phân mục trống, {text_len} ký tự)")
            continue

        print(f"\n🔍 [Trang {p_num}/{total_pages}] Đang bóc tách bằng Gemini 3.8 Flash...")
        pix = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5))
        img_bytes = pix.tobytes("jpeg")

        try:
            records = tech.extract_page(img_bytes, p_num, total_pages)
            if records:
                valid_records = []
                for r in records:
                    sku = r.get("sku")
                    if sku and sku not in existing_skus:
                        existing_skus.add(sku)
                        existing_products.append(r)
                        valid_records.append(r)
                        newly_added += 1
                        print(f"    ✓ Phát hiện SKU mới: [{sku}] - {r.get('product_name')}")
                    else:
                        print(f"    ⚠ Trùng SKU: {sku} (bỏ qua)")

                if valid_records and ws:
                    try:
                        append_products(ws, valid_records)
                        print(f"    📊 Đã đồng bộ {len(valid_records)} sản phẩm lên Google Sheets")
                    except Exception as se:
                        print(f"    ⚠ Lỗi đồng bộ Sheets: {se}")

                # Lưu cache ngay sau mỗi trang
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(existing_products, f, ensure_ascii=False, indent=2)

            else:
                print(f"    Không tìm thấy mã sản phẩm trên trang {p_num}.")

        except Exception as e:
            print(f"    ❌ Lỗi bóc tách trang {p_num}: {e}")

        # Nghỉ 4 giây giữa các trang để không chạm giới hạn 15 RPM của Gemini
        time.sleep(4)

    doc.close()
    print("\n" + "=" * 60)
    print(f"🎉 HOÀN THÀNH QUÉT TOÀN BỘ CATALOGUE!")
    print(f"Tổng số sản phẩm mới bóc tách được: {newly_added}")
    print(f"Tổng số sản phẩm trong cơ sở dữ liệu hiện tại: {len(existing_products)}")
    print("=" * 60)

if __name__ == "__main__":
    run_full_scan()

