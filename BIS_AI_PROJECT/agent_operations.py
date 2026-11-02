"""
BIS Textile AI - Agent Operations (Operations & Safety Gate)
Responsible for:
- Google Sheets Master synchronization (23 standard columns)
- Haravan Guard enforcement:
  * NEVER edit, overwrite, or delete products created before 2026-10-20
  * Only sync rows with status == APPROVED
  * Always publish as hidden (published: false)
  * Update PUSHED_TO_HARAVAN + Haravan Product ID + Audit Log
"""
import os
import sys
import re
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

import requests
import gspread

from config import (
    HARAVAN_TOKEN,
    HARAVAN_SHOP,
    HARAVAN_PUSH_ENABLED,
    SPREADSHEET_NAME,
    SPREADSHEET_ID_OR_URL,
    SHEET_PRODUCTS,
    SERVICE_ACCOUNT_FILE,
    PRODUCT_COLUMNS,
    STATUS_EXTRACTED,
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_PUSHED,
)
from sheets_manager import get_client, get_or_create_spreadsheet, init_products_sheet, append_products

HARAVAN_API_BASE = "https://apis.haravan.com/com"
HARAVAN_SAFETY_CUTOFF_DATE = "2026-10-20"


import unicodedata

def remove_accents(input_str: str) -> str:
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

def extract_core_numbers(s: str) -> set:
    if not s:
        return set()
    return set(re.findall(r'\b\d{4,6}\b', str(s)))

def tokenize_technical_text(text: str) -> set:
    if not text:
        return set()
    clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', str(text).lower())
    stop_words = {'and', 'the', 'for', 'with', 'cac', 'cua', 'cho', 'sach', 'tap', 'vai', 'mau', 'san', 'pham', 'aatcc'}
    return {w for w in clean.split() if len(w) > 2 and w not in stop_words}

def is_duplicate_product(p: dict, existing_store_items: list) -> tuple[bool, str, str]:
    """
    Hệ thống phát hiện trùng chuẩn xác cao kết hợp đọc full nội dung chi tiết (Deep Content De-duplication):
    - Tier 1: Trùng mã SKU chính xác trong danh sách Variant SKU trên sàn Haravan.
    - Tier 2: Trùng mã SKU trong tên Variant (Option/Title của Variant chứa SKU).
    - Tier 3: Trùng mã SKU xuất hiện dưới dạng từ/token độc lập trong URL handle, tiêu đề hoặc tags trên sàn.
    - Tier 4: Trùng mã SKU xuất hiện trong toàn bộ nội dung chi tiết bài viết (body_html / body_plain).
    - Tier 5: Trùng mã số tiêu chuẩn cốt lõi (Core Number >= 5 chữ số: e.g. 03026 từ 03026A/B) xuất hiện độc lập trong URL/tiêu đề hoặc nội dung chi tiết.
    - Tier 6: Trùng khớp cụm thuật ngữ kỹ thuật tiếng Anh độc bản đặc trưng của sản phẩm (e.g. gray scale color change, gray scale staining, light transmission verification fabric, spray tester funnel, spray tester nozzle) bên trong bài viết hoặc tiêu đề sản phẩm.
    """
    if not p or not existing_store_items:
        return False, "", ""

    sku = str(p.get("sku", "")).strip().upper()
    if not sku:
        return False, "", ""
    sku_low = sku.lower()
    name_en = str(p.get("product_name_en", "")).strip()

    pat_token = rf'(?:^|[\s,;:\(\)\[\]/#"\'<>–—_-])({re.escape(sku_low)})(?:$|[\s,;:\(\)\[\]/#"\'<>–—_-])'

    # Clean English title keywords
    en_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', name_en.lower()).strip()
    tokens_en = [w for w in en_clean.split() if len(w) > 3 and w not in ["standard", "aatcc", "test", "testing", "textile", "order", "item", "procedur", "international"]]

    core_num = re.sub(r'[A-Za-z]+$', '', sku)

    for item in existing_store_items:
        it_url = item.get("url", f"/products/{item.get('handle', '')}")
        it_title = str(item.get("title", "")).strip()
        it_handle = str(item.get("handle", "")).strip()
        it_tags = item.get("tags", [])
        it_tags_str = " ".join(it_tags) if isinstance(it_tags, list) else str(it_tags)
        tag_list_upper = [str(t).strip().upper() for t in (it_tags if isinstance(it_tags, list) else str(it_tags).split(","))]

        b_html = str(item.get("body_html", "") or "")
        b_plain = str(item.get("body_plain", "") or "")
        b_clean = re.sub(r'<[^>]+>', ' ', b_html)
        full_content = f"{it_title} {it_handle} {b_plain} {b_clean} {it_tags_str}".lower()

        # 1. Tier 1: Exact Variant SKU match
        variant_skus = [str(v).strip().upper() for v in item.get("variants_skus", []) if v]
        if "variants" in item and isinstance(item.get("variants"), list):
            for v in item.get("variants"):
                v_s = str(v.get("sku", "")).replace("#", "").strip().upper()
                if v_s and v_s not in variant_skus:
                    variant_skus.append(v_s)
        if sku in variant_skus:
            return True, it_url, f"Trùng mã SKU chính xác '{sku}' với sản phẩm '{it_title}'"

        # 2. Tier 2: Variant title match
        if "variants" in item and isinstance(item.get("variants"), list):
            v_titles = [str(v.get("title", "")).upper() for v in item.get("variants") if v.get("title")]
            if any(sku in vt for vt in v_titles):
                return True, it_url, f"Trùng mã SKU '{sku}' trong tên Variant của '{it_title}'"

        # 3. Tier 3: SKU token in handle, title or tags
        if re.search(pat_token, it_handle.lower()) or re.search(pat_token, it_title.lower()) or sku in tag_list_upper:
            return True, it_url, f"Mã SKU '{sku}' xuất hiện trong tên/URL của '{it_title}'"

        # 4. Tier 4: SKU token anywhere in full body content (body_html / body_plain)
        if re.search(pat_token, full_content):
            return True, it_url, f"Mã SKU '{sku}' xuất hiện trong toàn bộ nội dung chi tiết bài viết (body_html) của '{it_title}'"

        # 5. Tier 5: Core numeric code (e.g. 03026 trong 03026A/B khớp với sách 03026)
        if len(core_num) >= 5:
            pat_core = rf'(?:^|[\s,;:\(\)\[\]/#"\'<>–—_-])({re.escape(core_num.lower())})(?:$|[\s,;:\(\)\[\]/#"\'<>–—_-])'
            if re.search(pat_core, it_handle.lower()) or re.search(pat_core, it_title.lower()):
                return True, it_url, f"Trùng mã số cốt lõi '{core_num}' với '{it_title}'"
            if re.search(pat_core, full_content) and "aatcc" in full_content:
                return True, it_url, f"Mã số cốt lõi '{core_num}' xuất hiện trong toàn bộ nội dung bài viết '{it_title}'"

        # 6. Tier 6: High-precision technical phrase match (độc bản đặc thù)
        if len(tokens_en) >= 2:
            match_cnt = sum(1 for w in tokens_en if w in full_content)
            if match_cnt == len(tokens_en):
                return True, it_url, f"Khớp cụm tên kỹ thuật tiếng Anh ({' '.join(tokens_en)}) trong bài viết '{it_title}'"

    return False, "", ""

class AgentOperations:
    def __init__(self, storage_dir: str | Path | None = None):
        self.storage_dir = Path(storage_dir) if storage_dir else Path(__file__).parent.resolve()
        self.sa_path = self.storage_dir / SERVICE_ACCOUNT_FILE
        self.sync_log_path = self.storage_dir / "haravan_sync_log.json"

    # ── Google Sheets Management ──────────────────────────────────────────────
    def _get_sa_arg(self) -> str | None:
        return str(self.sa_path) if self.sa_path.exists() else None

    def connect_sheets(self) -> Tuple[Optional[gspread.Spreadsheet], Optional[gspread.Worksheet]]:
        """Connect and initialize Google Sheets structure with safe exception handling."""
        try:
            return init_products_sheet(self._get_sa_arg())
        except Exception as e:
            print(f"⚠️ [Agent_Operations] Google Sheets connection notice: {e}")
            return None, None

    def load_products_from_sheet(self) -> List[dict]:
        """Load all products from Google Sheets PRODUCTS tab with fallback."""
        try:
            client = get_client(self._get_sa_arg())
            ss = get_or_create_spreadsheet(client)
            ws = ss.worksheet(SHEET_PRODUCTS)
            return ws.get_all_records()
        except Exception as e:
            print(f"⚠️ [Agent_Operations] Cannot fetch from Google Sheets: {e}")
            return []

    def update_product_status_in_sheet(self, sku: str, new_status: str, notes: str = "", haravan_id: str = ""):
        """Update a product's status, notes, or haravan_id in Google Sheets with fallback."""
        try:
            client = get_client(self._get_sa_arg())
            ss = get_or_create_spreadsheet(client)
            ws = ss.worksheet(SHEET_PRODUCTS)
            records = ws.get_all_records()

            status_col = PRODUCT_COLUMNS.index("status") + 1
            notes_col = PRODUCT_COLUMNS.index("notes") + 1
            hid_col = PRODUCT_COLUMNS.index("haravan_product_id") + 1
            updated_at_col = PRODUCT_COLUMNS.index("updated_at") + 1

            now = datetime.utcnow().isoformat() + "Z"

            for idx, r in enumerate(records, start=2):
                if str(r.get("sku")).strip() == str(sku).strip():
                    ws.update_cell(idx, status_col, new_status)
                    ws.update_cell(idx, updated_at_col, now)
                    if notes:
                        ws.update_cell(idx, notes_col, notes)
                    if haravan_id:
                        ws.update_cell(idx, hid_col, str(haravan_id))
                    print(f"  ✓ [Agent_Operations] Updated Google Sheet row {idx} (SKU {sku}) -> {new_status}")
                    return True
            return False
        except Exception as e:
            print(f"⚠️ [Agent_Operations] Google Sheets update skipped ({e}). Local cache intact.")
            return False

    def check_and_deduplicate_sheets(self, products_cache: List[dict] | None = None) -> dict:
        """
        Quét và đối soát kiểm tra trùng toàn diện:
        1. Đối soát trùng SKU với các sản phẩm đang bán thực tế trên website bistextile.com (từ bistextile_existing_products.json).
           -> Nếu trùng, tự động KHÓA trạng thái = REJECTED, kèm cảnh báo nguồn link URL.
        2. Quét toàn bộ dòng trên Google Sheets Master:
           -> Phát hiện và lọc sạch các dòng trùng mã SKU, giữ lại dòng có dữ liệu chuẩn/mới nhất.
           -> Đồng bộ cập nhật trạng thái mới nhất lên Sheet.
        3. Tự động chuẩn hóa và lưu sạch vào extracted_products_cache.json.
        """
        start_time = time.time()
        print("\n🔍 [Agent_Operations] Bắt đầu quét đối soát và lọc trùng Google Sheets & bistextile.com...")

        # 1. Tải danh mục sản phẩm đang chạy trên bistextile.com
        existing_store_file = self.storage_dir / "bistextile_existing_products.json"
        existing_store_items = []
        if existing_store_file.exists():
            try:
                with open(existing_store_file, "r", encoding="utf-8") as f:
                    existing_store_items = json.load(f)
            except Exception as e:
                print(f"⚠️ [Agent_Operations] Không thể đọc bistextile_existing_products.json: {e}")

        # Hàm kiểm tra trùng trên website bistextile.com dùng hàm đa tầng nội dung
        def check_web_duplicate(sku_str: str) -> tuple[bool, str, str]:
            if not sku_str or not existing_store_items:
                return False, "", ""
            p_dummy = {"sku": sku_str}
            # Tìm trong cache nếu có thông tin sản phẩm đầy đủ
            for p_item in products:
                if str(p_item.get("sku", "")).strip().upper() == str(sku_str).strip().upper():
                    p_dummy = p_item
                    break
            return is_duplicate_product(p_dummy, existing_store_items)
            sku_clean = str(sku_str).strip().lower()
            for it in existing_store_items:
                t = str(it.get("title", "")).lower()
                u = str(it.get("url", "")).lower()
                if sku_clean in t or sku_clean in u:
                    return True, it.get("url", "")
            return False, ""

        # 2. Tải hoặc sử dụng danh sách sản phẩm hiện tại
        products = list(products_cache) if products_cache else []
        cache_file = self.storage_dir / "extracted_products_cache.json"
        if not products and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    products = json.load(f)
            except Exception:
                products = []

        # 3. Lọc trùng nội bộ trong cache và khóa trùng web
        deduped_cache_dict = {}
        website_dups_locked = []

        for p in products:
            sku = str(p.get("sku", "")).strip()
            if not sku:
                continue

            # Kiểm tra trùng website thông qua đa tầng nội dung & SKU
            is_dup, match_url, reason = is_duplicate_product(p, existing_store_items)
            if is_dup:
                p["status"] = STATUS_REJECTED
                p["notes"] = f"CẢNH BÁO: Đã tồn tại trên website bistextile.com ({match_url}) - {reason}"
                if sku not in website_dups_locked:
                    website_dups_locked.append(sku)
            else:
                if p.get("status") == STATUS_REJECTED:
                    p["status"] = STATUS_EXTRACTED
                    p["notes"] = f"Trích xuất trực tiếp từ Catalogue AATCC Trang {p.get('source_page', '1')}. SKU: {sku}."
                    p.pop("haravan_matched_id", None)
                    p.pop("haravan_matched_status", None)

            sku_key = sku.upper()
            if sku_key not in deduped_cache_dict:
                deduped_cache_dict[sku_key] = p
            else:
                # Nếu đã có trong danh sách, ưu tiên giữ bản APPROVED
                existing_p = deduped_cache_dict[sku_key]
                if p.get("status") == STATUS_APPROVED and existing_p.get("status") != STATUS_APPROVED:
                    deduped_cache_dict[sku_key] = p

        clean_products = list(deduped_cache_dict.values())
        sheet_dups_removed = 0
        connected_sheet = False
        sheet_url = ""

        # 4. Kiểm tra và lọc trùng trực tiếp trên Google Sheets (nếu kết nối được)
        try:
            client = get_client(self._get_sa_arg())
            ss = get_or_create_spreadsheet(client)
            ws = ss.worksheet(SHEET_PRODUCTS)
            connected_sheet = True
            sheet_url = ss.url

            all_values = ws.get_all_values()
            if len(all_values) > 1:
                headers = [str(h).strip().lower() for h in all_values[0]]
                sku_idx = headers.index("sku") if "sku" in headers else -1
                status_idx = headers.index("status") if "status" in headers else -1
                notes_idx = headers.index("notes") if "notes" in headers else -1

                sheet_rows_dict = {}

                for row in all_values[1:]:
                    if not row or not any(row):
                        continue
                    row_sku = str(row[sku_idx]).strip().upper() if sku_idx >= 0 and len(row) > sku_idx else ""
                    if not row_sku:
                        continue

                    # Kiểm tra trùng web cho dòng sheet
                    dup_res = check_web_duplicate(row_sku)
                    is_dup = dup_res[0]
                    match_url = dup_res[1]
                    reason = dup_res[2] if len(dup_res) > 2 else "Trùng mã/nội dung trên web"
                    if is_dup and status_idx >= 0 and len(row) > status_idx:
                        row[status_idx] = STATUS_REJECTED
                        if notes_idx >= 0:
                            if len(row) <= notes_idx:
                                row.extend([""] * (notes_idx - len(row) + 1))
                            row[notes_idx] = f"CẢNH BÁO: Đã tồn tại trên website bistextile.com ({match_url}) - {reason}"

                    if row_sku not in sheet_rows_dict:
                        sheet_rows_dict[row_sku] = row
                    else:
                        sheet_dups_removed += 1
                        existing_row = sheet_rows_dict[row_sku]
                        if status_idx >= 0 and len(row) > status_idx and row[status_idx] == STATUS_APPROVED:
                            sheet_rows_dict[row_sku] = row

                # Nếu có dòng trùng trên Sheet hoặc có sản phẩm bị khóa trùng, ghi đè lại dữ liệu sạch
                if sheet_dups_removed > 0 or website_dups_locked:
                    new_values = [all_values[0]] + list(sheet_rows_dict.values())
                    ws.clear()
                    ws.update("A1", new_values)
                    print(f"  ✓ [Agent_Operations] Đã dọn dẹp Google Sheet: loại bỏ {sheet_dups_removed} dòng trùng!")

        except Exception as e:
            print(f"ℹ️ [Agent_Operations] Quét Google Sheets qua mạng tạm dừng ({e}). Đã tối ưu hóa và lọc trùng toàn bộ bộ nhớ đệm cục bộ.")

        # 5. Lưu lại dữ liệu sạch vào cache file
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(clean_products, f, ensure_ascii=False, indent=2)

        # Đồng bộ vào repo git nếu có
        git_cache = Path("c:/Users/Dell/bis-ai-project/BIS_AI_PROJECT/extracted_products_cache.json")
        if git_cache.parent.exists():
            try:
                with open(git_cache, "w", encoding="utf-8") as f:
                    json.dump(clean_products, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        elapsed = round(time.time() - start_time, 2)
        summary = {
            "success": True,
            "connected_sheet": connected_sheet,
            "sheet_url": sheet_url,
            "total_products": len(clean_products),
            "website_duplicates_locked": len(website_dups_locked),
            "sheet_duplicates_removed": sheet_dups_removed,
            "locked_skus": website_dups_locked,
            "clean_products": clean_products,
            "duration_seconds": elapsed,
        }
        print(f"✓ [Agent_Operations] Hoàn tất đối soát: {len(clean_products)} SP hợp lệ, {len(website_dups_locked)} trùng web đã khóa, {sheet_dups_removed} dòng trùng Sheet đã lọc ({elapsed}s)")
        return summary

    def scan_live_haravan_and_web(self, products_cache: List[dict] | None = None) -> dict:
        """
        Quét trực tiếp thời gian thực từ:
        1. Haravan API: https://apis.haravan.com/com/products.json (Quét toàn bộ: Đã đăng, Đã ẩn)
        2. Website công khai: https://bistextile.com/collections/all/products.json
        -> Đối chiếu, phân loại chính xác: Đã đăng, Đã ẩn, hay Mới hoàn toàn.
        -> Tự động cập nhật vào extracted_products_cache.json và bistextile_existing_products.json.
        """
        import re
        start_time = time.time()
        print("\n🌐 [Agent_Operations] Bắt đầu quét Live Haravan API & bistextile.com/collections/all...")

        # 1. Quét Haravan API toàn bộ phân trang
        haravan_products = []
        page = 1
        while True:
            url = f"{HARAVAN_API_BASE}/products.json?page={page}&limit=50"
            try:
                r = requests.get(url, headers=self._haravan_headers(), timeout=15)
                if r.status_code != 200:
                    break
                data = r.json().get("products", [])
                if not data:
                    break
                haravan_products.extend(data)
                if len(data) < 50:
                    break
                page += 1
                time.sleep(0.2)
            except Exception as e:
                print(f"  ⚠ Lỗi kết nối Haravan API (page {page}): {e}")
                break

        # 2. Quét Website công khai bistextile.com/collections/all
        web_products = []
        page = 1
        while True:
            url = f"https://bistextile.com/collections/all/products.json?page={page}&limit=50"
            try:
                r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                if r.status_code != 200:
                    break
                data = r.json().get("products", [])
                if not data:
                    break
                web_products.extend(data)
                if len(data) < 50:
                    break
                page += 1
                time.sleep(0.2)
            except Exception as e:
                print(f"  ⚠ Lỗi kết nối collections/all (page {page}): {e}")
                break

        # Tổng hợp danh mục sàn (Bao gồm full nội dung body_html, body_plain và tags để đọc chi tiết)
        unified_store = []
        seen_handles = set()
        for h in haravan_products:
            handle = str(h.get("handle", "")).strip()
            seen_handles.add(handle)
            v_skus = [str(v.get("sku", "")).replace("#", "").strip() for v in h.get("variants", []) if v.get("sku")]
            is_pub = bool(h.get("published_at"))
            unified_store.append({
                "id": h.get("id"),
                "title": h.get("title"),
                "handle": handle,
                "url": f"/products/{handle}",
                "published": is_pub,
                "status_str": "ĐÃ ĐĂNG" if is_pub else "ĐÃ ẨN",
                "variants_skus": v_skus,
                "variants": h.get("variants", []),
                "tags": h.get("tags", []),
                "body_html": h.get("body_html", "") or "",
                "body_plain": h.get("body_plain", "") or "",
                "created_at": h.get("created_at"),
                "updated_at": h.get("updated_at")
            })

        for w in web_products:
            handle = str(w.get("handle", "")).strip()
            if handle not in seen_handles:
                seen_handles.add(handle)
                v_skus = [str(v.get("sku", "")).replace("#", "").strip() for v in w.get("variants", []) if v.get("sku")]
                unified_store.append({
                    "id": w.get("id"),
                    "title": w.get("title"),
                    "handle": handle,
                    "url": f"/products/{handle}",
                    "published": True,
                    "status_str": "ĐÃ ĐĂNG",
                    "variants_skus": v_skus,
                    "variants": w.get("variants", []),
                    "tags": w.get("tags", []),
                    "body_html": w.get("body_html", "") or "",
                    "body_plain": re.sub(r'<[^>]+>', ' ', w.get("body_html", "") or ""),
                    "created_at": w.get("created_at"),
                    "updated_at": w.get("updated_at")
                })

        # Lưu lại bản cập nhật mới nhất vào bistextile_existing_products.json
        if unified_store:
            store_file = self.storage_dir / "bistextile_existing_products.json"
            try:
                with open(store_file, "w", encoding="utf-8") as f:
                    json.dump(unified_store, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        # 3. Đối soát với danh sách sản phẩm bóc tách
        products = list(products_cache) if products_cache else []
        cache_file = self.storage_dir / "extracted_products_cache.json"
        if not products and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    products = json.load(f)
            except Exception:
                products = []

        matched = []
        unmatched = []

        for p in products:
            sku = str(p.get("sku", "")).strip()
            if not sku:
                continue
            sku_low = sku.lower()

            is_dup, match_url, reason = is_duplicate_product(p, unified_store)
            if is_dup:
                p["status"] = STATUS_REJECTED
                # Tìm item tương ứng để lấy ID
                match_item = next((it for it in unified_store if it.get("url") == match_url or it.get("handle") in match_url), unified_store[0] if unified_store else {})
                stt_txt = match_item.get("status_str", "ĐÃ ĐĂNG")
                p["notes"] = f"CẢNH BÁO: Đã có trên Haravan/Website ({stt_txt} - {match_url}) - {reason}"
                p["haravan_matched_id"] = match_item.get("id")
                p["haravan_matched_status"] = stt_txt
                matched.append({
                    "sku": sku,
                    "product_name": p.get("product_name"),
                    "status_str": stt_txt,
                    "url": match_item.get("url", match_url),
                    "haravan_id": match_item.get("id")
                })
            else:
                if p.get("status") == STATUS_REJECTED:
                    p["status"] = STATUS_EXTRACTED
                    p["notes"] = f"Trích xuất trực tiếp từ Catalogue AATCC Trang {p.get('source_page', '1')}. SKU: {sku}."
                    p.pop("haravan_matched_id", None)
                    p.pop("haravan_matched_status", None)
                unmatched.append(sku)

        # Lưu lại cache
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

        git_cache = Path("c:/Users/Dell/bis-ai-project/BIS_AI_PROJECT/extracted_products_cache.json")
        if git_cache.parent.exists():
            try:
                with open(git_cache, "w", encoding="utf-8") as f:
                    json.dump(products, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        elapsed = round(time.time() - start_time, 2)
        res = {
            "success": True,
            "total_haravan": len(haravan_products),
            "total_web": len(web_products),
            "total_published": sum(1 for p in haravan_products if p.get("published_at")),
            "total_hidden": sum(1 for p in haravan_products if not p.get("published_at")),
            "matched_count": len(matched),
            "unmatched_count": len(unmatched),
            "matched_details": matched,
            "clean_products": products,
            "duration_seconds": elapsed
        }
        print(f"✓ [Agent_Operations] Live scan xong: {len(haravan_products)} SP Haravan, {len(matched)} trùng đã khóa REJECTED, {len(unmatched)} SP mới ({elapsed}s)")
        return res

    # ── Haravan Guard & Synchronization ───────────────────────────────────────
    def _haravan_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {HARAVAN_TOKEN}",
            "Content-Type": "application/json",
            "X-Haravan-Shop": HARAVAN_SHOP,
        }

    def check_haravan_guard(self, existing_haravan_product: dict) -> bool:
        """
        Enforce Haravan Guard:
        Tuyệt đối KHÔNG sửa, KHÔNG ghi đè, KHÔNG xóa bất kỳ sản phẩm nào có ngày tạo trước 20/10/2026.
        Returns True if safe to proceed, False if protected.
        """
        created_at_str = existing_haravan_product.get("created_at", "")
        if created_at_str:
            # ISO date compare
            created_date = created_at_str[:10]
            if created_date < HARAVAN_SAFETY_CUTOFF_DATE:
                print(f"  🛡️ [Haravan Guard] BLOCKED: Sản phẩm ID {existing_haravan_product.get('id')} tạo ngày {created_date} trước mốc an toàn {HARAVAN_SAFETY_CUTOFF_DATE}!")
                return False
        return True

    def sync_approved_to_haravan(self, approved_products: List[dict] = None) -> List[dict]:
        """
        Scan and push ONLY APPROVED products to Haravan.
        - published: false (Luôn ẩn)
        - Guard against historical products before 2026-10-20
        - Update PUSHED_TO_HARAVAN and log
        """
        if not approved_products:
            # Load from Google Sheets
            all_records = self.load_products_from_sheet()
            approved_products = [p for p in all_records if p.get("status") == STATUS_APPROVED]

        if not approved_products:
            print("ℹ️ [Agent_Operations] Không có sản phẩm nào ở trạng thái APPROVED để đẩy Haravan.")
            return []

        print(f"\n🚀 [Agent_Operations] Bắt đầu đẩy {len(approved_products)} sản phẩm APPROVED lên Haravan (chế độ ẩn)...")
        results = []
        from agent_technical import AgentTechnical
        tech_agent = AgentTechnical(self.storage_dir)

        for p in approved_products:
            sku = p.get("sku")
            title = p.get("product_name") or p.get("product_name_en")
            body_html = p.get("custom_html") or tech_agent.build_7_block_html(p)

            # Đảm bảo handle không bị lỗi và an toàn
            clean_sku = re.sub(r"[^a-zA-Z0-9_-]", "", str(sku).lower()).strip()
            handle = f"sp-{clean_sku}" if clean_sku else f"sp-{int(time.time())}"

            payload = {
                "product": {
                    "title": title,
                    "handle": handle,
                    "body_html": body_html,
                    "vendor": p.get("brand") or p.get("vendor") or "BIS Textile",
                    "product_type": p.get("category") or "Vật tư thử nghiệm",
                    "published": False,  # BẮT BUỘC LUÔN ẨN
                    "published_scope": "global",
                    "tags": f"AATCC,Tài liệu tiêu chuẩn,{p.get('category', '')}",
                    "options": [
                        {
                            "name": "Title",
                            "values": ["Default Title"]
                        }
                    ],
                    "variants": [
                        {
                            "sku": sku,
                            "price": 0,
                            "title": "Default Title",
                            "option1": "Default Title",
                            "inventory_quantity": 9999,
                            "fulfillment_service": "manual",
                        }
                    ],
                }
            }

            try:
                # In live mode or test mode
                resp = requests.post(
                    f"{HARAVAN_API_BASE}/products.json",
                    headers=self._haravan_headers(),
                    json=payload,
                    timeout=20,
                )

                if resp.status_code in [200, 201]:
                    h_prod = resp.json().get("product", {})
                    h_id = str(h_prod.get("id"))
                    print(f"  ✓ Đẩy thành công SKU {sku} -> Haravan ID: {h_id} (published: false)")
                    
                    # Update Sheet
                    self.update_product_status_in_sheet(sku, STATUS_PUSHED, notes="Đã tạo ẩn thành công trên Haravan", haravan_id=h_id)
                    results.append({"sku": sku, "status": "SUCCESS", "haravan_id": h_id})
                else:
                    err_msg = resp.text[:200]
                    print(f"  ⚠ Haravan API trả về {resp.status_code}: {err_msg}")
                    results.append({"sku": sku, "status": "API_ERROR", "error": err_msg})

            except Exception as e:
                print(f"  ⚠ Lỗi kết nối Haravan khi đẩy SKU {sku}: {e}")
                results.append({"sku": sku, "status": "NETWORK_ERROR", "error": str(e)})

            time.sleep(0.5)  # Rate limiting

        self._record_sync_log(results)
        return results

    def _record_sync_log(self, sync_results: List[dict]):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "batch_size": len(sync_results),
            "results": sync_results
        }
        logs = []
        if self.sync_log_path.exists():
            try:
                logs = json.load(open(self.sync_log_path, encoding="utf-8"))
            except Exception:
                pass
        logs.append(log_entry)
        with open(self.sync_log_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

