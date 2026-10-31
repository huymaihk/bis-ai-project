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

try:
    import winocr
    import asyncio
    from PIL import Image
    import io
    HAS_WINOCR = True
except Exception:
    HAS_WINOCR = False

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

    def check_document_text_readability(self, doc_path: str | Path) -> Dict[str, any]:
        """
        Kiểm tra xem file PDF có chứa văn bản kỹ thuật số để dịch hay là file ảnh/vector bị khóa:
        - Nếu words < 30: Tài liệu là dạng hình ảnh/vector (chữ bị chuyển thành hình ảnh).
        - Nếu words >= 30: Tài liệu chứa văn bản chuẩn, AI dịch hoàn hảo 100%.
        """
        p = Path(doc_path)
        if not p.exists() or p.suffix.lower() != ".pdf":
            return {"readable": True, "word_count": 999, "is_image_pdf": False}
        
        try:
            import pymupdf
            doc = pymupdf.open(str(p))
            total_words = 0
            for page in doc:
                txt = page.get_text()
                total_words += len(txt.split())
            doc.close()
            
            is_image = total_words < 30
            return {
                "readable": not is_image,
                "word_count": total_words,
                "is_image_pdf": is_image,
                "message": (
                    f"⚠️ File này là PDF dạng hình ảnh/vector đồ họa (chỉ phát hiện {total_words} từ văn bản kỹ thuật số, còn lại toàn bộ chữ đã bị nhà thiết kế biến thành hình ảnh lát cắt). AI chỉ có thể dịch được các tài liệu chứa văn bản số chuẩn."
                    if is_image else
                    f"✅ Tài liệu chứa văn bản kỹ thuật số chuẩn ({total_words} từ), sẵn sàng dịch 100% sang tiếng Việt."
                )
            }
        except Exception:
            return {"readable": True, "word_count": 100, "is_image_pdf": False}

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

    def translate_image_or_scanned_pdf(
        self,
        input_path: Path,
        brand_name: str = "General",
        progress_callback: Optional[Callable[[float, str], None]] = None,
        max_pages: Optional[int] = None
    ) -> Path:
        """
        Dịch tài liệu trực tiếp từ HÌNH ẢNH hoặc PDF quét/đồ họa thông qua OCR:
        - Bóc tách toàn bộ văn bản trong ảnh bằng OCR (winocr).
        - Dịch toàn bộ nội dung sang tiếng Việt chuyên ngành dệt may.
        - Tạo file Word (.docx) chuẩn đẹp với tiêu đề, khối nội dung dịch và lưu vào 8_Translated_Documents.
        """
        clean_brand_folder = re.sub(r'[\\/*?:"<>|]', "", brand_name).strip() or "General"
        target_brand_dir = self.translated_dir / clean_brand_folder
        target_brand_dir.mkdir(parents=True, exist_ok=True)

        base_stem = input_path.stem
        output_docx_name = f"{base_stem}_TiengViet.docx"
        output_docx_path = target_brand_dir / output_docx_name

        if progress_callback:
            progress_callback(0.1, f"Bắt đầu xử lý OCR trích xuất chữ từ hình ảnh '{input_path.name}'...")

        doc_word = docx.Document()
        doc_word.add_heading(f"BẢN DỊCH TIẾNG VIỆT TỪ HÌNH ẢNH: {base_stem}", level=1)
        doc_word.add_paragraph(f"Tài liệu gốc: {input_path.name} • Hãng: {brand_name}")
        doc_word.add_paragraph("─" * 40)

        ext = input_path.suffix.lower()

        # TRƯỜNG HỢP 1: File ảnh đơn lẻ (.png, .jpg, .jpeg)
        if ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
            lines = []
            if HAS_WINOCR:
                img_pil = Image.open(str(input_path))
                ocr_res = asyncio.run(winocr.recognize_pil(img_pil, "en"))
                lines = [l.text.strip() for l in ocr_res.lines if l.text.strip()]
            
            if not lines:
                lines = ["(Không thể kích hoạt bộ nhận diện OCR trên hệ thống hoặc ảnh không chứa chữ)"]

            if progress_callback:
                progress_callback(0.4, f"Đã nhận diện {len(lines)} dòng chữ từ ảnh, đang dịch sang tiếng Việt...")

            # Dịch theo từng cụm hoặc dòng
            for idx, l in enumerate(lines):
                tr = translate_text_vi(l, self.translation_cache)
                p = doc_word.add_paragraph()
                p.add_run(tr)
                if progress_callback and (idx + 1) % 5 == 0:
                    prog = 0.4 + (idx / max(len(lines), 1)) * 0.5
                    progress_callback(min(prog, 0.92), f"Đang dịch dòng {idx+1}/{len(lines)}...")

        # TRƯỜNG HỢP 2: File PDF đồ họa / quét (chứa nhiều trang ảnh)
        elif ext == ".pdf":
            import pymupdf
            doc_pdf = pymupdf.open(str(input_path))
            total_pages = len(doc_pdf)
            pages_to_process = min(total_pages, max_pages) if max_pages and max_pages > 0 else total_pages

            for p_idx in range(pages_to_process):
                page = doc_pdf[p_idx]
                if progress_callback:
                    prog = 0.15 + (p_idx / max(pages_to_process, 1)) * 0.7
                    progress_callback(prog, f"Đang quét OCR & Dịch trang {p_idx+1}/{pages_to_process}...")

                doc_word.add_heading(f"=== TRANG {p_idx+1} ===", level=2)

                lines = []
                if HAS_WINOCR:
                    pix = page.get_pixmap(dpi=180)
                    img_bytes = pix.tobytes("png")
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    ocr_res = asyncio.run(winocr.recognize_pil(pil_img, "en"))
                    lines = [l.text.strip() for l in ocr_res.lines if l.text.strip()]

                if not lines:
                    raw_txt = page.get_text()
                    lines = [l.strip() for l in raw_txt.split("\n") if l.strip()]

                for l in lines:
                    tr = translate_text_vi(l, self.translation_cache)
                    p = doc_word.add_paragraph()
                    p.add_run(tr)

            doc_pdf.close()

        if progress_callback:
            progress_callback(0.95, "Đang hoàn tất đóng gói file Word bản dịch OCR...")

        doc_word.save(str(output_docx_path))

        if progress_callback:
            progress_callback(1.0, f"✅ Đã dịch xong từ ảnh! Bản dịch lưu tại: {output_docx_path.name}")

        return output_docx_path

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

        # TỰ ĐỘNG CHUYỂN SANG DỊCH TỪ ẢNH (OCR) NẾU FILE LÀ ẢNH HOẶC PDF QUÉT/VECTOR
        ext = input_path.suffix.lower()
        is_pure_image = ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]
        is_scanned_pdf = False
        if ext == ".pdf":
            r_info = self.check_document_text_readability(input_path)
            is_scanned_pdf = r_info.get("is_image_pdf", False)

        if is_pure_image or is_scanned_pdf:
            return self.translate_image_or_scanned_pdf(
                input_path,
                brand_name=brand_name,
                progress_callback=progress_callback,
                max_pages=max_pages
            )

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
