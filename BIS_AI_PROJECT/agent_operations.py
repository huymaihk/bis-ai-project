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

def is_duplicate_product(p, existing_store_items):
    from product_quality import match_product
    result = match_product(p, existing_store_items)
    # Legacy callers treat True as a lock: include uncertain matches for safety,
    # explicitly distinguish them in the reason and never call them confirmed duplicates.
    return result["state"] != "NO_MATCH", result["url"], result["state"] + ": " + result["reason"]

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
                    from gspread.utils import rowcol_to_a1
                    edits = []
                    for row_number, original in enumerate(all_values[1:], 2):
                        row_sku = str(original[sku_idx]).strip().upper() if sku_idx >= 0 and len(original)>sku_idx else ""
                        cleaned = sheet_rows_dict.get(row_sku)
                        if cleaned:
                            for col in (status_idx, notes_idx):
                                if col >= 0 and col < len(cleaned) and (col >= len(original) or original[col] != cleaned[col]):
                                    edits.append({"range":rowcol_to_a1(row_number,col+1),"values":[[cleaned[col]]]})
                    if edits:
                        ws.batch_update(edits, value_input_option="RAW")
                    sheet_dups_removed = 0  # Rows are retained; only status and notes were updated.
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
        from safe_publish import scan_store
        from persistent_memory import atomic_json
        from product_quality import match_product
        try:
            live = scan_store(self._haravan_headers())
        except Exception as exc:
            return {"success":False,"error":"Đối soát live chưa hoàn tất: "+type(exc).__name__,
                    "clean_products":products_cache or [],"matched_details":[],
                    "matched_count":0,"unmatched_count":0,"total_haravan":0,
                    "total_web":0,"total_published":0,"total_hidden":0,"duration_seconds":0}
        unified = []
        for item in live:
            unified.append(dict(item, url="/products/"+str(item.get("handle") or ""),
                                published=bool(item.get("published_at")),
                                status_str="ĐÃ ĐĂNG" if item.get("published_at") else "ĐÃ ẨN"))
        products = list(products_cache) if products_cache is not None else []
        cache = self.storage_dir/"extracted_products_cache.json"
        if products_cache is None and cache.exists():
            products = json.loads(cache.read_text(encoding="utf-8"))
        matched=[];review=[];unmatched=[]
        for product in products:
            result = match_product(product, unified)
            product["duplicate_check"] = result
            if result["state"] == "MATCH":
                # Never turn a manual rejection into an approval on a future scan.
                product["status"] = STATUS_REJECTED
                product["notes"] = "MATCH: "+result["reason"]+" "+result["url"]
                product["haravan_matched_id"] = result["id"]
                matched.append({"sku":product.get("sku"),"url":result["url"],
                                "haravan_id":result["id"],"status_str":"ĐÃ CÓ",
                                "product_name":product.get("product_name")})
            elif result["state"] == "REVIEW":
                review.append(product.get("sku"))
            else:
                unmatched.append(product.get("sku"))
        atomic_json(self.storage_dir/"bistextile_existing_products.json", unified)
        atomic_json(cache, products)
        return {"success":True,"total_haravan":len(live),"total_web":0,
                "total_published":sum(bool(p.get("published_at")) for p in live),
                "total_hidden":sum(not p.get("published_at") for p in live),
                "matched_count":len(matched),"matched_details":matched,
                "review_count":len(review),"review_skus":review,
                "unmatched_count":len(unmatched),"clean_products":products,"duration_seconds":0}

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
        return bool(created_at_str)

    def sync_approved_to_haravan(self, approved_products: List[dict] = None) -> List[dict]:
        """
        Scan and push ONLY APPROVED products to Haravan.
        - published: false (Luôn ẩn)
        - Guard against historical products before 2026-10-20
        - Update PUSHED_TO_HARAVAN and log
        """
        from safe_publish import publish_batch
        if approved_products is None:
            approved_products = self.load_products_from_sheet()
        results = publish_batch(approved_products, self.storage_dir)
        self._record_sync_log(results)
        for result in results:
            if result["status"] == "SUCCESS":
                try:
                    self.update_product_status_in_sheet(result["sku"], STATUS_PUSHED,
                        notes="Đã xác minh bản nháp Haravan", haravan_id=result["haravan_id"])
                except Exception:
                    result["sheet_status"] = "PENDING"
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

