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

    def connect_sheets(self) -> Tuple[gspread.Spreadsheet, gspread.Worksheet]:
        """Connect and initialize Google Sheets structure."""
        return init_products_sheet(self._get_sa_arg())

    def load_products_from_sheet(self) -> List[dict]:
        """Load all products from Google Sheets PRODUCTS tab."""
        client = get_client(self._get_sa_arg())
        ss = get_or_create_spreadsheet(client)
        ws = ss.worksheet(SHEET_PRODUCTS)
        return ws.get_all_records()

    def update_product_status_in_sheet(self, sku: str, new_status: str, notes: str = "", haravan_id: str = ""):
        """Update a product's status, notes, or haravan_id in Google Sheets."""
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

