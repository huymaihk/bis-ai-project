"""
BIS Textile AI - Agent Knowledge (Reference Documents & Standards Archive Department)
Responsible for:
- Archiving standard books, manuals, catalogues, CO (Origin), CQ (Quality), COC (Conformity)
- Organizing training media (reference photos, testing lab videos)
- Indexing knowledge to feed contextual memory into Gemini Multimodal agents
"""
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

class AgentKnowledge:
    def __init__(self, workspace_dir: str | Path | None = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path(__file__).parent.resolve()
        self.gdrive_storage = self.workspace_dir / "Google_Drive_Storage"
        self.gdrive_storage.mkdir(parents=True, exist_ok=True)
        
        # Thư mục lưu trữ trực tiếp trên Google Drive phân loại rõ ràng
        self.subdirs = {
            "catalogues": self.gdrive_storage / "1_Catalogues",
            "manuals": self.gdrive_storage / "2_Manuals_Standards",
            "standards": self.gdrive_storage / "2_Manuals_Standards",
            "certificates": self.gdrive_storage / "3_Certificates_CO_CQ",
            "media": self.gdrive_storage / "7_Training_Videos"
        }
        for d in self.subdirs.values():
            d.mkdir(parents=True, exist_ok=True)

        self.manifest_file = self.gdrive_storage / "knowledge_manifest.json"
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> List[dict]:
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        
        # Mẫu mặc định sẵn có nếu chưa có file
        initial_items = [
            {
                "id": "DOC-AATCC-2024",
                "title": "AATCC Technical Manual 2024 (Official Standard)",
                "category": "standards",
                "filename": "AATCC_Technical_Manual_2024.pdf",
                "scope": "Phương pháp thử nghiệm độ bền màu, co rút và tính chất cơ lý vải dệt.",
                "verified": True,
                "added_at": "2026-10-25 10:00:00"
            },
            {
                "id": "DOC-COC-AATCC",
                "title": "Chứng nhận Hợp chuẩn COC / CO Nhà phân phối BIS Textile",
                "category": "certificates",
                "filename": "AATCC_Authorized_Distributor_COC.pdf",
                "scope": "Chứng thư đại lý phân phối chính thức ủy quyền tại Việt Nam.",
                "verified": True,
                "added_at": "2026-10-26 14:30:00"
            },
            {
                "id": "DOC-CAT-SAMPLE",
                "title": "Catalogue Thiết bị & Vật tư Dệt may BIS Textile Sample",
                "category": "catalogues",
                "filename": "catalogue_sample.pdf",
                "scope": "Tổng hợp 17 sản phẩm thiết bị và sách tiêu chuẩn phòng thí nghiệm.",
                "verified": True,
                "added_at": "2026-10-28 09:15:00"
            }
        ]
        self._save_manifest(initial_items)
        return initial_items

    def _save_manifest(self, data: List[dict]):
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def register_document(self, title: str, category: str, filename: str, scope: str, file_bytes: bytes = None) -> dict:
        """Register a new standard document into knowledge vault."""
        target_dir = self.subdirs.get(category, self.vault_dir)
        target_path = target_dir / filename
        
        if file_bytes:
            with open(target_path, "wb") as f:
                f.write(file_bytes)

        doc_entry = {
            "id": f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": title,
            "category": category,
            "filename": filename,
            "scope": scope,
            "verified": True,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.manifest.append(doc_entry)
        self._save_manifest(self.manifest)
        return doc_entry

    def get_knowledge_summary_for_prompt(self) -> str:
        """Returns consolidated knowledge guidelines to inject into Gemini agents."""
        lines = ["CƠ SỞ DỮ LIỆU TÀI LIỆU TIÊU CHUẨN ĐÃ THẨM ĐỊNH (KNOWLEDGE VAULT):"]
        for doc in self.manifest:
            lines.append(f"- [{doc['category'].upper()}] {doc['title']}: {doc['scope']}")
        return "\n".join(lines)

    @property
    def storage_root(self):
        return self.gdrive_storage

    def ensure_storage_structure(self):
        for d in self.subdirs.values():
            d.mkdir(parents=True, exist_ok=True)
        return self.subdirs

    def get_knowledge_summary(self) -> dict:
        return {
            "total_documents": len(self.manifest),
            "categories": list(self.subdirs.keys()),
            "storage_path": str(self.gdrive_storage)
        }


