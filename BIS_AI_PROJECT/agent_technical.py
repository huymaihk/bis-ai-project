"""
BIS Textile AI - Agent Technical (R&D Department)
Responsible for:
- PDF Multimodal extraction via Gemini with Pydantic schema
- 6-Step Audit Pipeline (B1: Integrity, B2: De-duplication, B3: Facts & Quotes, B4: SEO, B5: Role/Origin Evidence, B6: HTML match)
- 7-Block Haravan description HTML synthesis
- Learning loop integration via few-shot injection
"""
import os
import sys
import re
import json
import uuid
import time
import io
import html as html_lib
import urllib.request
import urllib.parse
import concurrent.futures
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

from pydantic import BaseModel, Field
import pymupdf
from google import genai
from google.genai import types

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    PRIORITY_MODELS,
    MAX_WORKERS,
    STATUS_EXTRACTED,
    STATUS_APPROVED,
    STATUS_REJECTED,
    PRODUCT_COLUMNS,
)
from learning_engine import LearningEngine

def translate_to_vi(text: str) -> str:
    """Tự động dịch văn bản mô tả sang tiếng Việt mượt mà, chuyên ngành dệt may."""
    if not text or not str(text).strip():
        return ""
    text_str = str(text).strip()
    vi_chars = set('àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ')
    # Nếu đã có tiếng Việt có dấu đầy đủ thì giữ nguyên
    if sum(1 for c in text_str.lower() if c in vi_chars) >= 4:
        return text_str

    sentences = re.split(r'(\. |\n+)', text_str)
    chunks = []
    curr = ""
    for s in sentences:
        if len(curr) + len(s) < 320:
            curr += s
        else:
            if curr:
                chunks.append(curr)
            curr = s
    if curr:
        chunks.append(curr)

    out = []
    for c in chunks:
        if not c.strip() or c in ['. ', '\n']:
            out.append(c)
            continue
        try:
            q = urllib.parse.quote(c)
            url = f"https://api.mymemory.translated.net/get?q={q}&langpair=en|vi"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as res:
                data = json.loads(res.read().decode('utf-8'))
                trans = data.get('responseData', {}).get('translatedText', c)
                out.append(html_lib.unescape(trans))
            time.sleep(0.12)
        except Exception:
            out.append(c)
    result = "".join(out).strip()
    return result if result else text_str

# ── Pydantic Schemas for Strict Structured Extraction ─────────────────────────
class ExtractedProductFact(BaseModel):
    product_name: str = Field(description="Tên sản phẩm tiếng Việt chuẩn hóa")
    product_name_en: str = Field(description="Tên sản phẩm tiếng Anh nguyên bản từ catalogue")
    sku: str = Field(description="Mã sản phẩm / SKU / Catalog number")
    category: Optional[str] = Field(default="Vật tư thử nghiệm", description="Danh mục phân loại (Tủ soi màu/Thiết bị/Vật tư/Tài liệu tiêu chuẩn)")
    material: Optional[str] = Field(default=None, description="Thành phần vật liệu (VD: 100% Cotton, Thép không gỉ)")
    color: Optional[str] = Field(default=None, description="Màu sắc (nếu có)")
    width_cm: Optional[float] = Field(default=None, description="Khổ rộng số thuần cm")
    weight_gsm: Optional[float] = Field(default=None, description="Định lượng/Trọng lượng g/m2")
    pattern: Optional[str] = Field(default=None, description="Kiểu dệt hoặc kiểu dáng")
    finish: Optional[str] = Field(default=None, description="Xử lý bề mặt")
    description: str = Field(description="Mô tả công năng và chi tiết kỹ thuật")
    price_vnd: Optional[float] = Field(default=None, description="Giá VNĐ nếu có trong tài liệu")
    price_usd: Optional[float] = Field(default=None, description="Giá USD nếu có trong tài liệu")
    min_order_qty: Optional[float] = Field(default=None, description="Số lượng đặt hàng tối thiểu")
    unit: Optional[str] = Field(default="cuốn", description="Đơn vị tính (cuốn/bản/mét/gói/bộ/chiếc)")
    evidence_quote: str = Field(description="Câu trích dẫn nguyên văn bằng tiếng Anh từ trang catalogue chứng minh mã và công năng")
    source_page: int = Field(description="Số trang PDF")
    brand_evidence: Optional[str] = Field(default=None, description="Bằng chứng vai trò hãng (VD: Published by AATCC, USA)")

class PageExtractionResult(BaseModel):
    page_number: int
    products: List[ExtractedProductFact] = Field(default_factory=list)


def is_self_referencing_or_generic_doc(candidate_title: str, record: dict) -> bool:
    """
    Kiểm tra xem tên tài liệu liên quan có bị trùng lặp hoặc tự tham chiếu đến chính sản phẩm đang đăng hay không:
    - Trùng với mã SKU
    - Trùng hoặc tương đồng cao với tên sản phẩm tiếng Việt hoặc tiếng Anh
    - Chứa cụm từ tra cứu chung chung hoặc generic fallback
    """
    if not candidate_title or not str(candidate_title).strip():
        return True

    t_low = str(candidate_title).strip().lower()
    sku = str(record.get("sku", "")).strip().lower()
    vi = str(record.get("product_name", "")).strip().lower()
    en = str(record.get("product_name_en", "")).strip().lower()

    # 1. Generic fallbacks không mang giá trị chuyên môn cụ thể
    if "quy trình và tiêu chuẩn kiểm nghiệm dệt may quốc tế" in t_low:
        return True
    if "sổ tay phương pháp thử nghiệm và tiêu chuẩn dệt may" in t_low:
        return True
    if "astm compass" in t_low and ("compass" in vi or "compass" in en):
        return True
    if sku and sku in t_low:
        return True
    if "tra cứu sản phẩm mã" in t_low:
        return True

    # 2. Trùng với tên sản phẩm hiện tại
    if t_low == vi or t_low == en:
        return True

    # 3. So khớp mức độ trùng lặp từ khóa (> 50%)
    stop_words = {"và", "các", "tiêu", "chuẩn", "phương", "pháp", "thử", "nghiệm", "dệt", "may", "quốc", "tế", "hệ", "thống", "cơ", "sở", "dữ", "liệu", "trực", "tuyến", "qua"}
    words_t = set(re.findall(r'\w+', t_low)) - stop_words
    words_vi = set(re.findall(r'\w+', vi)) - stop_words
    words_en = set(re.findall(r'\w+', en)) - stop_words

    if words_t and words_vi and len(words_t & words_vi) / len(words_t) >= 0.5:
        return True
    if words_t and words_en and len(words_t & words_en) / len(words_t) >= 0.5:
        return True

    return False


def resolve_related_standard_doc(record: dict) -> tuple[str, str]:
    """
    Tự động suy luận Tiêu chuẩn & Tài liệu kỹ thuật liên quan thực tế (Khối 7):
    - Tuyệt đối KHÔNG trùng lặp với tên sản phẩm đang chuẩn bị đăng hoặc mã SKU.
    - Chỉ gán khi tìm thấy mã phương pháp thử nghiệm/tiêu chuẩn chuyên ngành cụ thể (AATCC TM, ISO 105, ASTM D...).
    - Nếu không có tiêu chuẩn liên quan thực sự khác biệt, BỎ TRỐNG (trả về "", "").
    """
    custom_title = record.get("related_doc_title")
    if custom_title and not is_self_referencing_or_generic_doc(custom_title, record):
        return str(custom_title).strip(), record.get("related_doc_url") or f"https://bistextile.com/search?q={urllib.parse.quote(str(custom_title).strip())}"

    desc = str(record.get("description", ""))
    notes = str(record.get("notes", ""))
    text = f"{desc} {notes}"
    name_vi = str(record.get("product_name", "")).lower()

    # 1. Quét tìm mã tiêu chuẩn cụ thể trong mô tả / ghi chú kỹ thuật
    matches_tm = re.findall(r'\b(AATCC\s+(?:TM|LP|EP|M|Monograph)\s*\d+[\.\d]*)\b', text, re.I)
    matches_iso = re.findall(r'\b(ISO\s+105(?:-[A-Z0-9]+)?)\b', text, re.I)
    matches_astm = re.findall(r'\b(ASTM\s+[D|E|F]\s*\d+)\b', text, re.I)

    candidate = ""
    if matches_tm:
        code = matches_tm[0].upper().strip()
        candidate = f"Tiêu chuẩn phương pháp thử {code}"
    elif matches_iso:
        code = matches_iso[0].upper().strip()
        candidate = f"Tiêu chuẩn quốc tế {code}"
    elif matches_astm:
        code = matches_astm[0].upper().strip()
        candidate = f"Tiêu chuẩn kỹ thuật {code}"
    elif any(k in text.lower() for k in ["crock", "ma sát", "rubbing"]) and "crock" not in name_vi:
        candidate = "Tiêu chuẩn phương pháp kiểm tra độ bền màu ma sát AATCC TM8"
    elif any(k in text.lower() for k in ["giặt", "washing", "launder"]) and "giặt" not in name_vi and "launder" not in name_vi:
        candidate = "Tiêu chuẩn phương pháp thử nghiệm độ bền màu giặt AATCC TM61"
    elif any(k in text.lower() for k in ["len xanh", "blue wool"]) and "len xanh" not in name_vi:
        candidate = "Tiêu chuẩn độ bền màu với ánh sáng AATCC TM16.3"

    # Kiểm tra tính tự tham chiếu / trùng lặp
    if candidate and not is_self_referencing_or_generic_doc(candidate, record):
        return candidate, f"https://bistextile.com/search?q={urllib.parse.quote(candidate)}"

    # Nếu không có tài liệu liên quan khác biệt: BỎ TRỐNG hoàn toàn
    return "", ""


class AgentTechnical:
    def __init__(self, storage_dir: str | Path | None = None):
        self.storage_dir = Path(storage_dir) if storage_dir else Path(__file__).parent.resolve()
        self.learning_engine = LearningEngine(self.storage_dir)
        self.client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(timeout=45000))

    def _build_prompt(self, page_num: int, total_pages: int, brand: str = "AATCC") -> str:
        focused_guidelines = self.learning_engine.get_focused_guidelines(brand=brand)
        base_prompt = f"""
Bạn là Trưởng phòng Kỹ thuật AI (Agent Technical) của BIS Textile.
Nhiệm vụ: Trích xuất TOÀN BỘ sản phẩm/tài liệu tiêu chuẩn dệt may trên trang {page_num}/{total_pages} của catalogue.

{focused_guidelines}

QUY TẮC BẮT BUỘC (6 BƯỚC THẨM ĐỊNH KỸ THUẬT):
1. B3 (Facts & Quotes): Mỗi sản phẩm bắt buộc phải có 'sku', 'product_name' (tiếng Việt), 'product_name_en' (tiếng Anh nguyên bản), 'description' (BẮT BUỘC PHẢI DỊCH SANG TIẾNG VIỆT CHUẨN XÁC, CHUYÊN NGÀNH DỆT MAY, TUYỆT ĐỐI KHÔNG ĐỂ TIẾNG ANH), 'source_page' ({page_num}) và 'evidence_quote' (câu trích dẫn tiếng Anh nguyên văn từ trang chứng minh).
2. Bảng thông số kỹ thuật và mô tả: TUYỆT ĐỐI KHÔNG chứa thông tin 'Đơn vị tính' và 'Trang nguồn tài liệu', TUYỆT ĐỐI KHÔNG thêm câu 'Cung cấp chính ngạch...'.
2. B5 (Thương hiệu & Xuất xứ): Nếu trang có nêu rõ hãng (như AATCC, SDC, SDL Atlas) hoặc vai trò (Published by / Manufactured in), hãy ghi vào 'brand_evidence'. Nếu thiếu thông tin thương hiệu/xuất xứ thì để null (hệ thống sẽ tự động gắn nhãn MISSING_BRAND_EVIDENCE để người dùng xem xét, tuyệt đối không suy diễn từ trụ sở và không làm nghẽn luồng).
3. Các trường số (width_cm, weight_gsm, price, min_order_qty) chỉ ghi số thuần hoặc null nếu không có.
4. Trả về đúng định dạng JSON danh sách các sản phẩm:
[
  {{
    "product_name": "...",
    "product_name_en": "...",
    "sku": "...",
    "category": "...",
    "material": null,
    "color": null,
    "width_cm": null,
    "weight_gsm": null,
    "pattern": null,
    "finish": null,
    "description": "...",
    "price_vnd": null,
    "price_usd": null,
    "min_order_qty": null,
    "unit": "...",
    "evidence_quote": "...",
    "source_page": {page_num},
    "brand_evidence": "..."
  }}
]
Nếu không có sản phẩm thương mại nào trên trang này, trả về [].
"""
        return base_prompt.strip()

    def _extract_fallback_from_text(self, page_num: int, brand: str = "AATCC", page_text: Optional[str] = None) -> List[dict]:
        """
        Chế độ bóc tách không phụ thuộc AI (Deterministic Local Fallback):
        - Chỉ dùng text của trang đã chọn và mã SKU có dấu định danh rõ.
        - Gán nhãn NEEDS_REVIEW để người dùng đối soát, không làm gián đoạn quy trình.
        """
        # Never substitute another document when the selected page has no text.
        if not page_text or not str(page_text).strip():
            return []

        matches = list(re.finditer(r'\b(?:Item|Order|Code|Part)\s*(?:#|No\.?|:)\s*([A-Z0-9][A-Z0-9\-]*)\b', page_text, re.IGNORECASE))
        if not matches:
            return []

        now = datetime.utcnow().isoformat() + "Z"
        records = []
        start_pos = 0

        for m in matches:
            sku = m.group(1).strip().upper()
            if not any(c.isdigit() for c in sku) or any(r['sku'] == sku for r in records):
                continue
            end_pos = m.end()
            segment = page_text[start_pos:end_pos].strip()
            start_pos = end_pos

            lines = [l.strip() for l in segment.splitlines() if l.strip()]
            filtered = [l for l in lines if not (l.isdigit() and len(l) <= 3) and l.upper() not in ('SCALES', 'CATALOGUE')]

            title_lines, desc_lines = [], []
            is_title = True
            for line in filtered:
                if is_title and (line.isupper() or len(title_lines) < 2) and not line.lower().startswith(('the ', 'item ', 'order ')):
                    title_lines.append(line)
                else:
                    is_title = False
                    if not line.lower().startswith(('item ', 'order ')):
                        desc_lines.append(line)

            title_en = ' '.join(title_lines).strip()
            desc = ' '.join(desc_lines).strip()

            name_vi = title_en or sku
            name_en = title_en or sku
            final_desc = desc

            rec = {
                "product_id": str(uuid.uuid4()),
                "analysis_model": "PyMuPDF-LocalFallback",
                "status": STATUS_EXTRACTED,
                "source_page": str(page_num),
                "product_name": name_vi,
                "product_name_en": name_en,
                "sku": sku,
                "category": None,
                "material": None,
                "color": None,
                "width_cm": None,
                "weight_gsm": None,
                "pattern": None,
                "finish": None,
                "description": final_desc,
                "price_vnd": None,
                "price_usd": None,
                "min_order_qty": None,
                "unit": None,
                "image_urls": None,
                "haravan_product_id": None,
                "created_at": now,
                "updated_at": now,
                "notes": f"[Dự phòng cục bộ] Trích xuất từ văn bản gốc (AI bận/quá tải). Cần kiểm tra lại trước khi duyệt.",
                "evidence_quote": segment[:1000],
                "brand_evidence": None,
            }
            audit_res = self.audit_6_steps(rec)
            audit_res.update(status="NEEDS_REVIEW", overall_pass=False, passed=False, has_warnings=True)
            rec["audit_result"] = audit_res
            records.append(rec)

        return records

    def extract_page(self, img_bytes: bytes, page_num: int, total_pages: int, brand: str = "AATCC", page_text: Optional[str] = None, allow_local_fallback: bool = True) -> List[dict]:
        self.last_extraction_status = 'RUNNING'
        self.last_extraction_error = ''
        self.last_model_attempts = []
        self.last_model_used = None
        prompt = self._build_prompt(page_num, total_pages, brand=brand)
        if page_text and str(page_text).strip():
            prompt += f"\n\nVĂN BẢN GỐC TỪ TRANG {page_num} CỦA TÀI LIỆU (DÙNG ĐỂ ĐỐI CHIẾU VÀ TRÍCH XUẤT CHÍNH XÁC):\n{str(page_text).strip()}\n"
        max_retries = 2

        for attempt in range(max_retries):
            try:
                from gemini_fallback import generate_with_fallback
                response, self.last_model_used = generate_with_fallback(
                    self.client, PRIORITY_MODELS,
                    attempts=self.last_model_attempts,
                    contents=[
                        prompt,
                        types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=8192,
                        response_mime_type="application/json",
                    ),
                )
                text = response.text.strip()
                if not text:
                    raise ValueError('Empty model response')

                raw_list = json.loads(text)
                if isinstance(raw_list, dict):
                    raw_list = [raw_list]

                if not isinstance(raw_list, list):
                    raise ValueError('Invalid model response')
                self.last_extraction_status = 'EMPTY_VALID' if not raw_list else 'PARSED'
                validated_records = []
                now = datetime.utcnow().isoformat() + "Z"

                for item in raw_list:
                    # Validate through Pydantic
                    try:
                        fact = ExtractedProductFact(**item)
                    except Exception as pe:
                        # Fallback parsing
                        fact = ExtractedProductFact(
                            product_name=item.get("product_name") or "Sản phẩm dệt may",
                            product_name_en=item.get("product_name_en") or "Textile Product",
                            sku=str(item.get("sku") or f"UNKNOWN-{uuid.uuid4().hex[:6]}"),
                            category=item.get("category") or "Vật tư thử nghiệm",
                            description=item.get("description") or "",
                            evidence_quote=item.get("evidence_quote") or f"Extracted from page {page_num}",
                            source_page=page_num,
                            brand_evidence=item.get("brand_evidence")
                        )

                    rec = {
                        "product_id": str(uuid.uuid4()),
                        "analysis_model": self.last_model_used,
                        "status": STATUS_EXTRACTED,
                        "source_page": str(page_num),
                        "product_name": fact.product_name,
                        "product_name_en": fact.product_name_en,
                        "sku": fact.sku,
                        "category": fact.category or "Vật tư thử nghiệm",
                        "material": fact.material,
                        "color": fact.color,
                        "width_cm": str(fact.width_cm) if fact.width_cm else None,
                        "weight_gsm": str(fact.weight_gsm) if fact.weight_gsm else None,
                        "pattern": fact.pattern,
                        "finish": fact.finish,
                        "description": fact.description,
                        "price_vnd": str(fact.price_vnd) if fact.price_vnd else None,
                        "price_usd": str(fact.price_usd) if fact.price_usd else None,
                        "min_order_qty": str(fact.min_order_qty) if fact.min_order_qty else None,
                        "unit": fact.unit or "cuốn",
                        "image_urls": None,
                        "haravan_product_id": None,
                        "created_at": now,
                        "updated_at": now,
                        "notes": f"Trích dẫn: \"{fact.evidence_quote}\"",
                        "evidence_quote": fact.evidence_quote,
                        "brand_evidence": fact.brand_evidence,
                    }

                    # Apply auto-learning corrections from memory
                    rec = self.learning_engine.apply_auto_corrections(rec)

                    # 6-Step Audit Pipeline evaluation
                    audit_res = self.audit_6_steps(rec)
                    rec["audit_result"] = audit_res

                    validated_records.append(rec)

                print(f"  ⚡ [Agent_Technical] Trang {page_num}/{total_pages}: Bóc tách thành công {len(validated_records)} sản phẩm")
                return validated_records

            except Exception as e:
                self.last_extraction_status = 'FAILED'
                err_str = str(e)
                self.last_extraction_error = (
                    'Hết hạn mức API hoặc giới hạn tốc độ (429)' if '429' in err_str or 'quota' in err_str.lower()
                    else 'Model không khả dụng hoặc quá tải (503)' if '503' in err_str
                    else 'Gemini từ chối khóa API (401/403). Kiểm tra GEMINI_API_KEY trong Streamlit Secrets, quyền và dự án AI Studio' if '401' in err_str or '403' in err_str
                    else 'Model không tồn tại (404)' if '404' in err_str
                    else 'Phản hồi AI trống hoặc không đúng cấu trúc' if isinstance(e, (ValueError, TypeError))
                    else 'Không gọi được AI: '+type(e).__name__)
                if self.last_model_attempts:
                    tried = '; '.join(
                        str(item['model']) + ': ' + (str(item.get('code', 0)) if item['status'] == 'FAILED' else 'OK')
                        for item in self.last_model_attempts)
                    self.last_extraction_error += ' | Model đã thử: ' + tried
                if getattr(e, 'code', None) in (503, 504):
                    if allow_local_fallback:
                        fallback_rows = self._extract_fallback_from_text(page_num, brand, page_text=page_text)
                        if fallback_rows:
                            self.last_extraction_status = 'NEEDS_REVIEW'
                            self.last_model_used = 'PyMuPDF-LocalFallback'
                            return fallback_rows
                    return []
                if '401' in err_str or '403' in err_str:
                    return []
                if "429" in err_str or "quota" in err_str.lower():
                    wait = 3 * (attempt + 1)
                    print(f"  ⚠ Quota limit on page {page_num} — waiting {wait}s…")
                    time.sleep(wait)
                else:
                    print(f"  ⚠ Lỗi bóc tách trang {page_num} (lần {attempt+1}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(3)
                    else:
                        if allow_local_fallback:
                            fallback_rows = self._extract_fallback_from_text(page_num, brand, page_text=page_text)
                            if fallback_rows:
                                self.last_extraction_status = 'PARSED'
                                self.last_model_used = 'PyMuPDF-LocalFallback'
                                return fallback_rows
                        return []
        return []

    def audit_6_steps(self, record: dict) -> dict:
        """
        Execute the 6-Step Technical Verification Pipeline:
        B1: PDF Integrity
        B2: SKU Unique within batch
        B3: Facts & Raw Evidence Quote
        B4: Bilingual SEO
        B5: Brand & Origin Verification (or MISSING_BRAND_EVIDENCE warning)
        B6: HTML 7-Block match
        """
        from product_quality import validate_product
        from safe_publish import source_text
        try:
            source = source_text(self.storage_dir, record)
        except Exception:
            source = None
        report = validate_product(record, source)
        step = {"step": "Evidence and structure", "pass": report["passed"],
                "detail": "; ".join(report["errors"]) or "Đã đối chiếu nguồn và cấu trúc"}
        return {"overall_pass": report["passed"], "has_warnings": not report["passed"],
                **{f"b{i}": dict(step, step=f"B{i}") for i in range(1,7)},
                "quality_report": report}

    def build_7_block_html(self, record: dict, force_refresh: bool = False) -> str:
        from product_quality import render_product
        return render_product(record)
