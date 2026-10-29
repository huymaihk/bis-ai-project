"""
BIS Textile AI - Agent Leader (Central Orchestrator)
Coordinates all departments:
- Agent_Technical (R&D / Extraction / 6-Step Audit / 7-Block HTML)
- Agent_Operations (Sheets Master / Haravan Guard / Safe Sync)
- Extensible Registry for future agents (Agent_Sales, Agent_Marketing, Agent_Warehouse)
"""
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import pymupdf

from agent_technical import AgentTechnical
from agent_operations import AgentOperations
from agent_marketing import AgentMarketing
from agent_knowledge import AgentKnowledge
from agent_media import AgentMedia
from learning_engine import LearningEngine

class AgentLeader:
    def __init__(self, workspace_dir: str | Path | None = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path(__file__).parent.resolve()
        
        # Initialize Departmental Sub-Agents
        self.technical_agent = AgentTechnical(self.workspace_dir)
        self.operations_agent = AgentOperations(self.workspace_dir)
        self.marketing_agent = AgentMarketing(self.workspace_dir)
        self.knowledge_agent = AgentKnowledge(self.workspace_dir)
        self.media_agent = AgentMedia(self.workspace_dir)
        self.learning_engine = LearningEngine(self.workspace_dir)

        # Department Registry (Plug & Play architecture)
        self.departments = {
            "technical": self.technical_agent,
            "operations": self.operations_agent,
            "marketing": self.marketing_agent,
            "knowledge": self.knowledge_agent,
            "media": self.media_agent,
            "sales": None,       # Ready to plug Agent_Sales
            "warehouse": None,   # Ready to plug Agent_Warehouse
        }

    def register_department(self, name: str, agent_instance):
        """Allows plugging in new departmental agents dynamically."""
        self.departments[name.lower()] = agent_instance
        print(f"🏢 [Agent_Leader] Phòng ban '{name}' đã được kết nối vào hệ sinh thái Multi-Agent.")

    def run_catalogue_pipeline(self, pdf_path: str, max_pages: Optional[int] = None, sync_to_sheets: bool = True) -> dict:
        """
        Orchestrate complete catalogue ingestion:
        1. Pre-flight check sheets with Agent_Operations
        2. Read PDF & execute 6-step audit with Agent_Technical
        3. Real-time stream to Google Sheets
        4. Cross-check against bistextile.com live products
        5. Generate executive summary report
        """
        start_time = time.time()
        print("=" * 65)
        print("  👑 [Agent_Leader] KHỞI ĐỘNG NHIỆM VỤ XỬ LÝ CATALOGUE DỆT MAY")
        print(f"  Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 65)

        pdf_path = str(Path(pdf_path).resolve())
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF không tồn tại: {pdf_path}")

        # Step 1: Operations Pre-flight
        ws = None
        if sync_to_sheets:
            print("\n👉 [Agent_Leader -> Agent_Operations] Khởi tạo bảng tính Google Sheets Master...")
            ss, ws = self.operations_agent.connect_sheets()
            print(f"   ✓ Sẵn sàng tại: {ss.url}")

        # Step 2: Technical Multimodal Extraction
        print("\n👉 [Agent_Leader -> Agent_Technical] Chuyển đổi PDF & Bóc tách có kiểm chứng 6 bước...")
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
        print(f"   Tài liệu gồm {total_pages} trang. Xử lý {pages_to_process} trang...")

        all_extracted_products = []
        for p_idx in range(pages_to_process):
            page = doc[p_idx]
            pix = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5))
            img_bytes = pix.tobytes("jpeg")
            
            records = self.technical_agent.extract_page(img_bytes, p_idx + 1, pages_to_process)
            
            if records:
                all_extracted_products.extend(records)
                # Stream to Google Sheets
                if ws:
                    from sheets_manager import append_products
                    append_products(ws, records)

        doc.close()

        # Step 3: De-duplication check against live store
        print("\n👉 [Agent_Leader -> Operations Guard] Kiểm tra đối chiếu chống trùng với bistextile.com...")
        existing_store_file = self.workspace_dir / "bistextile_existing_products.json"
        duplicates_count = 0
        if existing_store_file.exists():
            try:
                existing_items = json.load(open(existing_store_file, encoding="utf-8"))
                for p in all_extracted_products:
                    sku = p.get("sku")
                    matched = [e for e in existing_items if sku in e.get("title", "") or sku in e.get("url", "")]
                    if matched:
                        duplicates_count += 1
                        p["status"] = "REJECTED"
                        p["notes"] = f"CẢNH BÁO: Đã tồn tại trên website bistextile.com ({matched[0].get('url')})"
                        if ws:
                            self.operations_agent.update_product_status_in_sheet(sku, "REJECTED", p["notes"])
            except Exception as e:
                print(f"  ⚠ Lỗi kiểm tra trùng: {e}")

        elapsed = time.time() - start_time
        summary = {
            "status": "COMPLETED",
            "duration_seconds": round(elapsed, 1),
            "pages_processed": pages_to_process,
            "total_extracted": len(all_extracted_products),
            "duplicates_locked": duplicates_count,
            "ready_for_review": len(all_extracted_products) - duplicates_count,
            "cache_file": str(self.workspace_dir / "extracted_products_cache.json")
        }

        # Cache locally
        with open(summary["cache_file"], "w", encoding="utf-8") as f:
            json.dump(all_extracted_products, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 65)
        print("  🎉 [Agent_Leader] HOÀN THÀNH BÁO CÁO NHIỆM VỤ")
        print("=" * 65)
        print(f"  Thời gian thực hiện   : {summary['duration_seconds']}s")
        print(f"  Số sản phẩm bóc tách : {summary['total_extracted']}")
        print(f"  Đã khóa trùng web    : {summary['duplicates_locked']}")
        print(f"  Chờ BIS phê duyệt     : {summary['ready_for_review']}")
        print("=" * 65)
        return summary

    def request_haravan_sync(self) -> dict:
        """Leader authorizes Operations to sync approved products to Haravan."""
        print("\n👉 [Agent_Leader -> Agent_Operations] Ủy quyền đồng bộ các sản phẩm APPROVED lên Haravan...")
        results = self.operations_agent.sync_approved_to_haravan()
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "synced_count": len([r for r in results if r.get("status") == "SUCCESS"]),
            "details": results
        }

