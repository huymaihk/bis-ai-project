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

HARAVAN_API_BASE = "https://app.haravan.com/api/v1"
HARAVAN_SAFETY_CUTOFF_DATE = "2026-10-20"


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

        # Hàm kiểm tra trùng trên website bistextile.com
        def check_web_duplicate(sku_str: str) -> tuple[bool, str]:
            if not sku_str or not existing_store_items:
                return False, ""
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

            # Kiểm tra trùng website
            is_dup, match_url = check_web_duplicate(sku)
            if is_dup:
                p["status"] = STATUS_REJECTED
                p["notes"] = f"CẢNH BÁO: Đã tồn tại trên website bistextile.com ({match_url})"
                if sku not in website_dups_locked:
                    website_dups_locked.append(sku)

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
                    is_dup, match_url = check_web_duplicate(row_sku)
                    if is_dup and status_idx >= 0 and len(row) > status_idx:
                        row[status_idx] = STATUS_REJECTED
                        if notes_idx >= 0:
                            if len(row) <= notes_idx:
                                row.extend([""] * (notes_idx - len(row) + 1))
                            row[notes_idx] = f"CẢNH BÁO: Đã tồn tại trên website bistextile.com ({match_url})"

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
            body_html = tech_agent.build_7_block_html(p)

            payload = {
                "product": {
                    "title": title,
                    "body_html": body_html,
                    "vendor": p.get("vendor") or "BIS Textile",
                    "product_type": p.get("category") or "Vật tư thử nghiệm",
                    "published": False,  # BẮT BUỘC LUÔN ẨN
                    "tags": f"AATCC,Tài liệu tiêu chuẩn,{p.get('category', '')}",
                    "variants": [
                        {
                            "sku": sku,
                            "price": "0",
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

