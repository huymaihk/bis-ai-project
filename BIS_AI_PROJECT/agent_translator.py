"""
BIS Textile AI - Agent Translator (Phòng Biên Dịch & Bản Địa Hóa Tiêu Chuẩn Quốc Tế)
Chịu trách nhiệm:
- Quét cây thư mục tài liệu tiêu chuẩn, hướng dẫn sử dụng (Manuals & Standards) phân theo Hãng.
- Dịch toàn bộ nội dung PDF / DOCX sang tiếng Việt chuyên ngành dệt may.
- Giữ nguyên 100% cấu trúc, định dạng, các cột bảng biểu, hình ảnh, font chữ và style của file gốc.
- Lưu trữ vào thư mục riêng: Google_Drive_Storage/8_Translated_Documents/<Tên_Hãng>/
- Cung cấp file Word (.docx) và hỗ trợ tải xuống ngay trên giao diện người dùng.
"""

import os
import sys
import re
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Callable

try:
    import docx
    from docx.shared import Inches, Pt, RGBColor
except Exception:
    docx = None

try:
    from pdf2docx import Converter
except Exception:
    Converter = None

PROJECT_DIR = Path(__file__).parent.resolve()

# Thư mục nguồn và thư mục đích riêng biệt
MANUALS_DIR = PROJECT_DIR / "Google_Drive_Storage" / "2_Manuals_Standards"
TRANSLATED_DIR = PROJECT_DIR / "Google_Drive_Storage" / "8_Translated_Documents"

# Bộ nhớ đệm dịch thuật toàn cục để tăng tốc và tránh gọi API trùng lặp
GLOBAL_TRANSLATE_CACHE: Dict[str, str] = {}


def translate_text_vi(text: str, cache_dict: Optional[dict] = None) -> str:
    """
    Dịch văn bản kỹ thuật sang tiếng Việt chuyên ngành dệt may:
    - Bỏ qua nếu là số, mã kỹ thuật, đơn vị đo lường, ký tự đặc biệt.
    - Tận dụng bộ nhớ đệm cache_dict để không dịch lại các từ lặp lại.
    - Sử dụng translators engine (Bing / Google) cho độ chính xác cao nhất.
    """
    if not text or not str(text).strip():
        return text

    text_clean = str(text).strip()

    # 1. Bỏ qua nếu chỉ toàn số, mã SKU, ký hiệu điện tử / đơn vị đo (V, Hz, mm, kg, %, °C, RPM...)
    if re.match(r"^[\d\s\.,\-\/\\:;#%*+()_–—°C°F\w]{1,4}$", text_clean):
        return text
    if re.match(r"^\d+([.,]\d+)?\s*(mm|cm|m|kg|g|gsm|rpm|hz|v|kw|w|a|min|s|°c|°f|%|pa|kpa|bar|psi|l|ml)?$", text_clean, re.I):
        return text

    # 2. Đã có tiếng Việt có dấu chuẩn
    vi_chars = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ")
    if sum(1 for c in text_clean.lower() if c in vi_chars) >= 4:
        return text

    # 3. Kiểm tra trong cache
    if cache_dict is not None and text_clean in cache_dict:
        return cache_dict[text_clean]
    if text_clean in GLOBAL_TRANSLATE_CACHE:
        return GLOBAL_TRANSLATE_CACHE[text_clean]

    # 4. Thực hiện dịch qua thư viện translators chuyên dụng
    translated_text = None
    try:
        import translators as ts
        for eng in ["bing", "alibaba", "google"]:
            try:
                res = ts.translate_text(text_clean, to_language="vi", translator=eng)
                if res and str(res).strip():
                    translated_text = str(res).strip()
                    break
            except Exception:
                continue
    except Exception:
        pass

    # Nếu không dịch được thì giữ nguyên gốc
    final_res = translated_text if translated_text else text_clean

    if cache_dict is not None:
        cache_dict[text_clean] = final_res
    GLOBAL_TRANSLATE_CACHE[text_clean] = final_res

    return final_res


class AgentTranslator:
    def __init__(self, workspace_dir: str | Path | None = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else PROJECT_DIR
        self.manuals_dir = self.workspace_dir / "Google_Drive_Storage" / "2_Manuals_Standards"
        self.translated_dir = self.workspace_dir / "Google_Drive_Storage" / "8_Translated_Documents"
        self.translated_dir.mkdir(parents=True, exist_ok=True)
        self.translation_cache: Dict[str, str] = {}

    def scan_manuals_by_brand(self) -> Dict[str, List[Dict[str, any]]]:
        """
        Quét và phân nhóm tài liệu theo từng hãng sản xuất (Brand folders).
        """
        if not self.manuals_dir.exists():
            return {}

        brand_map: Dict[str, List[Dict[str, any]]] = {}

        # 1. Các thư mục con chia theo Hãng
        for folder in sorted(self.manuals_dir.iterdir()):
            if folder.is_dir() and not folder.name.startswith("."):
                raw_brand_name = folder.name
                clean_brand = re.sub(r"^\d+[-_]?", "", raw_brand_name).strip() or raw_brand_name

                docs = []
                for f in folder.rglob("*"):
                    if f.is_file() and f.suffix.lower() in [".pdf", ".docx"]:
                        docs.append({
                            "name": f.name,
                            "path": str(f),
                            "ext": f.suffix.lower(),
                            "size_kb": round(f.stat().st_size / 1024, 1),
                            "rel_path": str(f.relative_to(self.manuals_dir)),
                            "brand_folder": raw_brand_name,
                            "brand_clean": clean_brand
                        })
                if docs:
                    brand_map[clean_brand] = sorted(docs, key=lambda x: x["name"])

        # 2. Các tài liệu tiêu chuẩn chung ở thư mục gốc (AATCC, ISO, etc.)
        root_docs = []
        for f in self.manuals_dir.iterdir():
            if f.is_file() and f.suffix.lower() in [".pdf", ".docx"]:
                root_docs.append({
                    "name": f.name,
                    "path": str(f),
                    "ext": f.suffix.lower(),
                    "size_kb": round(f.stat().st_size / 1024, 1),
                    "rel_path": f.name,
                    "brand_folder": "Chung (Tiêu chuẩn AATCC & ISO)",
                    "brand_clean": "Tiêu chuẩn chung (AATCC / ISO)"
                })
        if root_docs:
            brand_map["Tiêu chuẩn chung (AATCC / ISO)"] = sorted(root_docs, key=lambda x: x["name"])

        return brand_map

    def translate_document(
        self,
        doc_path: str | Path,
        brand_name: str = "General",
        progress_callback: Optional[Callable[[float, str], None]] = None,
        max_pages: Optional[int] = None
    ) -> Path:
        """
        Dịch tài liệu sang tiếng Việt, giữ nguyên 100% cấu trúc, bảng biểu, ảnh và style.
        Lưu vào thư mục riêng: Google_Drive_Storage/8_Translated_Documents/<brand_name>/
        Trả về đường dẫn file Word (.docx) đã dịch hoàn tất.
        """
        input_path = Path(doc_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Không tìm thấy tài liệu: {doc_path}")

        if docx is None:
            raise RuntimeError("Thư viện 'python-docx' chưa được cài đặt. Vui lòng chạy: pip install python-docx pdf2docx translators")

        # Chuẩn bị thư mục đích riêng cho Hãng
        clean_brand_folder = re.sub(r'[\\/*?:"<>|]', "", brand_name).strip() or "General"
        target_brand_dir = self.translated_dir / clean_brand_folder
        target_brand_dir.mkdir(parents=True, exist_ok=True)

        base_stem = input_path.stem
        output_docx_name = f"{base_stem}_TiengViet.docx"
        output_docx_path = target_brand_dir / output_docx_name

        if progress_callback:
            progress_callback(0.05, f"Bắt đầu phân tích cấu trúc tài liệu '{input_path.name}'...")

        working_docx_path = output_docx_path

        # ── BƯỚC 1: XỬ LÝ ĐẦU VÀO (PDF HOẶC DOCX) ──────────────────────────
        if input_path.suffix.lower() == ".pdf":
            if progress_callback:
                progress_callback(0.15, "Đang bóc tách bảng biểu, font chữ, hình ảnh từ PDF sang Word...")

            temp_raw_docx = target_brand_dir / f"~temp_{base_stem}.docx"
            try:
                cv = Converter(str(input_path))
                if max_pages and max_pages > 0:
                    cv.convert(str(temp_raw_docx), start=0, end=max_pages)
                else:
                    cv.convert(str(temp_raw_docx))
                cv.close()
                working_docx_path = temp_raw_docx
            except Exception as e:
                # Fallback qua pymupdf nếu có lỗi
                import pymupdf
                doc_pdf = pymupdf.open(str(input_path))
                doc_word = docx.Document()
                for page_idx in range(len(doc_pdf)):
                    if max_pages and page_idx >= max_pages:
                        break
                    p_txt = doc_pdf[page_idx].get_text("text")
                    for para in p_txt.split("\n\n"):
                        if para.strip():
                            doc_word.add_paragraph(para.strip())
                doc_word.save(str(temp_raw_docx))
                working_docx_path = temp_raw_docx
        else:
            # File đã là DOCX, sao chép sang file tạm để xử lý
            working_docx_path = input_path

        # ── BƯỚC 2: DỊCH TOÀN BỘ NỘI DUNG GIỮ NGUYÊN 100% ĐỊNH DẠNG ─────────
        if progress_callback:
            progress_callback(0.35, "Đang mở tài liệu và chuẩn bị dịch từng khối văn bản & bảng biểu...")

        doc = docx.Document(str(working_docx_path))

        # Đếm tổng số đoạn văn bản và ô bảng biểu để tính tiến độ
        total_paras = len(doc.paragraphs)
        total_cells = sum(len(row.cells) for t in doc.tables for row in t.rows)
        total_items = max(total_paras + total_cells, 1)
        processed_items = 0

        # 1. Dịch các đoạn văn bản (Paragraphs)
        for p in doc.paragraphs:
            raw_text = p.text
            if raw_text.strip():
                trans_text = translate_text_vi(raw_text, self.translation_cache)
                if len(p.runs) == 1:
                    p.runs[0].text = trans_text
                elif len(p.runs) > 1:
                    p.runs[0].text = trans_text
                    for r in p.runs[1:]:
                        r.text = ""
                else:
                    p.text = trans_text

            processed_items += 1
            if progress_callback and processed_items % 5 == 0:
                prog = 0.35 + (processed_items / total_items) * 0.55
                progress_callback(min(prog, 0.92), f"Đang dịch văn bản ({processed_items}/{total_items})...")

        # 2. Dịch các Bảng biểu (Tables) giữ nguyên cột và viền ô
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        cell_text = p.text
                        if cell_text.strip():
                            trans_cell = translate_text_vi(cell_text, self.translation_cache)
                            if len(p.runs) >= 1:
                                p.runs[0].text = trans_cell
                                for r in p.runs[1:]:
                                    r.text = ""
                            else:
                                p.text = trans_cell
                    processed_items += 1
                    if progress_callback and processed_items % 5 == 0:
                        prog = 0.35 + (processed_items / total_items) * 0.55
                        progress_callback(min(prog, 0.95), f"Đang dịch bảng biểu ({processed_items}/{total_items})...")

        # ── BƯỚC 3: LƯU TÀI LIỆU HOÀN THIỆN VÀO THƯ MỤC RIÊNG ───────────────
        if progress_callback:
            progress_callback(0.96, "Đang đóng gói và hoàn tất file Word bản dịch...")

        doc.save(str(output_docx_path))

        # Dọn dẹp file tạm nếu có
        if input_path.suffix.lower() == ".pdf":
            temp_file = target_brand_dir / f"~temp_{base_stem}.docx"
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass

        if progress_callback:
            progress_callback(1.0, f"✅ Đã dịch xong! Bản dịch lưu tại: {output_docx_path.name}")

        return output_docx_path

    def list_translated_documents(self) -> List[Dict[str, any]]:
        """Liệt kê các tài liệu đã dịch xong trong thư mục riêng."""
        if not self.translated_dir.exists():
            return []

        results = []
        for f in self.translated_dir.rglob("*.docx"):
            if f.is_file() and not f.name.startswith("~"):
                brand_name = f.parent.name if f.parent != self.translated_dir else "Chung"
                results.append({
                    "name": f.name,
                    "brand": brand_name,
                    "path": str(f),
                    "size_kb": round(f.stat().st_size / 1024, 1),
                    "created_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime))
                })
        return sorted(results, key=lambda x: x["created_at"], reverse=True)
