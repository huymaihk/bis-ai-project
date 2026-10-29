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

    def scan_and_sync_drive_files(self) -> Dict[str, List[str]]:
        """
        Auto-scan all Google Drive Storage subdirectories and root folder for files dropped directly by user.
        Intelligently routes files dropped at root to appropriate folders:
        - BIS_BACKGROUND.png / *background* / *bg* -> 5_Studio_Backgrounds
        - *.pdf (catalogue) -> 1_Catalogues
        - Standards / Manuals -> 2_Manuals_Standards
        Auto-updates manifest and returns dict of detected files.
        """
        import shutil

        detected = {
            "catalogues": [],
            "manuals": [],
            "certificates": [],
            "product_images": [],
            "backgrounds": [],
            "media": []
        }
        existing_filenames = {d.get("filename") for d in self.manifest}

        # 0. Intelligent root scanning: If user dropped files directly into Google_Drive_Storage root
        root_dir = self.gdrive_storage
        if root_dir.exists():
            for root_file in root_dir.iterdir():
                if root_file.is_file() and root_file.name not in ["knowledge_manifest.json", "image_review_manifest.json"]:
                    fname_lower = root_file.name.lower()
                    # Check background images
                    if any(kw in fname_lower for kw in ["background", "bg", "nen", "studio"]) and root_file.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                        target = self.gdrive_storage / "5_Studio_Backgrounds" / root_file.name
                        shutil.copy2(root_file, target)
                    # Check catalogue pdfs
                    elif root_file.suffix.lower() == ".pdf":
                        if any(kw in fname_lower for kw in ["manual", "huong_dan", "standard", "tieuchuan"]):
                            target = self.subdirs["manuals"] / root_file.name
                        elif any(kw in fname_lower for kw in ["cert", "co", "cq", "chungnhan"]):
                            target = self.subdirs["certificates"] / root_file.name
                        else:
                            target = self.subdirs["catalogues"] / root_file.name
                        shutil.copy2(root_file, target)
                    elif root_file.suffix.lower() in [".jpg", ".png", ".jpeg"]:
                        target = self.gdrive_storage / "4_Product_Images" / root_file.name
                        shutil.copy2(root_file, target)

        # 0.1 Cross-check 4_Product_Images for background files like BIS_BACKGROUND.png
        img_dir = self.gdrive_storage / "4_Product_Images"
        bg_dir = self.gdrive_storage / "5_Studio_Backgrounds"
        bg_dir.mkdir(parents=True, exist_ok=True)
        if img_dir.exists():
            for p in list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpeg")):
                detected["product_images"].append(p.name)
                # Auto-bridge to backgrounds if name indicates background
                if any(kw in p.name.lower() for kw in ["background", "bg", "nen", "studio"]):
                    bg_target = bg_dir / p.name
                    if not bg_target.exists():
                        shutil.copy2(p, bg_target)

        # 1. Catalogues (1_Catalogues) - Quét đệ quy toàn bộ thư mục con
        cat_dir = self.subdirs["catalogues"]
        cat_dir.mkdir(parents=True, exist_ok=True)
        for p in cat_dir.rglob("*.pdf"):
            if not p.is_file(): continue
            detected["catalogues"].append(p.name)
            if p.name not in existing_filenames:
                size_mb = round(p.stat().st_size / (1024 * 1024), 2)
                self.manifest.append({
                    "id": f"DOC-CAT-{p.stem[:12]}",
                    "title": f"Catalogue: {p.name}",
                    "category": "catalogues",
                    "filename": p.name,
                    "scope": f"File Catalogue PDF phát hiện trực tiếp từ Google Drive ({size_mb} MB).",
                    "verified": True,
                    "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                existing_filenames.add(p.name)

        # 2. Manuals & Standards (2_Manuals_Standards) - Quét đệ quy toàn bộ thư mục con
        man_dir = self.subdirs["manuals"]
        man_dir.mkdir(parents=True, exist_ok=True)
        for p in list(man_dir.rglob("*.pdf")) + list(man_dir.rglob("*.docx")):
            if not p.is_file(): continue
            detected["manuals"].append(p.name)
            if p.name not in existing_filenames:
                brand_tag = f"[{p.parent.name}] " if p.parent != man_dir else ""
                self.manifest.append({
                    "id": f"DOC-MAN-{p.stem[:12]}",
                    "title": f"{brand_tag}Tài liệu tiêu chuẩn: {p.name}",
                    "category": "standards" if any(k in p.name.lower() for k in ["iso", "aatcc", "astm", "din", "g035", "lp1"]) else "manuals",
                    "filename": p.name,
                    "scope": f"Tài liệu / Tiêu chuẩn / Manual máy từ thư mục {p.parent.name}.",
                    "verified": True,
                    "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                existing_filenames.add(p.name)

        # 3. Certificates CO/CQ (3_Certificates_CO_CQ) - Quét đệ quy toàn bộ thư mục con
        cert_dir = self.subdirs["certificates"]
        cert_dir.mkdir(parents=True, exist_ok=True)
        for p in list(cert_dir.rglob("*.pdf")) + list(cert_dir.rglob("*.png")) + list(cert_dir.rglob("*.jpg")):
            if not p.is_file(): continue
            detected["certificates"].append(p.name)
            if p.name not in existing_filenames:
                self.manifest.append({
                    "id": f"DOC-CERT-{p.stem[:12]}",
                    "title": f"Chứng nhận CO/CQ: {p.name}",
                    "category": "certificates",
                    "filename": p.name,
                    "scope": f"Hồ sơ chứng nhận CO / CQ / COC thẩm định nguồn gốc.",
                    "verified": True,
                    "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                existing_filenames.add(p.name)

        # 4. Studio Backgrounds (5_Studio_Backgrounds)
        if bg_dir.exists():
            for p in list(bg_dir.rglob("*.jpg")) + list(bg_dir.rglob("*.png")) + list(bg_dir.rglob("*.jpeg")):
                if p.is_file(): detected["backgrounds"].append(p.name)

        # 5. Training Videos (7_Training_Videos)
        vid_dir = self.subdirs["media"]
        if vid_dir.exists():
            for p in list(vid_dir.rglob("*.mp4")) + list(vid_dir.rglob("*.mov")) + list(vid_dir.rglob("*.avi")):
                if p.is_file(): detected["media"].append(p.name)

        self._save_manifest(self.manifest)
        return detected



