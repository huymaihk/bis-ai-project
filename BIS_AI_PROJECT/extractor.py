"""
BIS Textile Pipeline - PDF Extractor using Gemini 1.5 Pro
Uses the new google-genai SDK (v2+).
"""
import os
import sys
import json
import uuid
import time
import io
import concurrent.futures
import threading
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_WORKERS, STATUS_EXTRACTED, PRODUCT_COLUMNS


def get_client() -> genai.Client:
    """Return authenticated Gemini client."""
    return genai.Client(api_key=GEMINI_API_KEY)


EXTRACTION_PROMPT = """
Bạn là chuyên gia trích xuất dữ liệu sản phẩm dệt may từ catalogue.

Hãy phân tích hình ảnh trang catalogue này và trích xuất TOÀN BỘ sản phẩm có trên trang.
Trả về JSON array, mỗi phần tử là một sản phẩm với các trường sau:

[
  {
    "product_name": "Tên sản phẩm tiếng Việt",
    "product_name_en": "Product name in English",
    "sku": "Mã SKU/sản phẩm nếu có",
    "category": "Danh mục (vải/sợi/phụ liệu/etc.)",
    "material": "Thành phần vải (VD: 100% Cotton, 70% Polyester 30% Cotton)",
    "color": "Màu sắc",
    "width_cm": "Khổ vải số thuần (cm, không kèm đơn vị)",
    "weight_gsm": "Trọng lượng số thuần (g/m2, không kèm đơn vị)",
    "pattern": "Kiểu dệt/hoa văn",
    "finish": "Xử lý bề mặt/hoàn tất",
    "description": "Mô tả chi tiết sản phẩm",
    "price_vnd": "Giá VNĐ số thuần nếu có",
    "price_usd": "Giá USD số thuần nếu có",
    "min_order_qty": "Số lượng đặt hàng tối thiểu (số thuần)",
    "unit": "Đơn vị tính (mét/kg/yard/cuộn/etc.)",
    "notes": "Ghi chú thêm"
  }
]

Quy tắc quan trọng:
- Nếu không có thông tin cho một trường, để null
- Các trường số chỉ trả về số thuần túy (không kèm đơn vị)
- Trả về [] nếu không có sản phẩm nào trên trang này
- CHỈ trả về JSON thuần túy, KHÔNG có markdown, không có ```json, không có giải thích
"""


def pdf_to_images(pdf_path: str) -> list[bytes] | None:
    """Convert PDF pages to JPEG bytes using PyMuPDF."""
    try:
        import pymupdf
        doc = pymupdf.open(pdf_path)
        images = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            mat = pymupdf.Matrix(1.5, 1.5)  # ~108 dpi
            pix = page.get_pixmap(matrix=mat)
            images.append(pix.tobytes("jpeg"))
        doc.close()
        print(f"  ✓ Converted {len(images)} page(s) to JPEG via PyMuPDF")
        return images
    except ImportError:
        print("  ⚠ PyMuPDF not found — falling back to Gemini File API (PDF direct upload)")
        return None
    except Exception as e:
        print(f"  ⚠ PDF conversion error: {e} — falling back to File API")
        return None


def extract_from_image(client: genai.Client, image_bytes: bytes, page_num: int) -> list[dict]:
    """Send one page image to Gemini and return parsed products."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[
                    EXTRACTION_PROMPT,
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                ),
            )
            text = response.text.strip()
            if not text:
                return []

            # Clean any stray formatting if needed
            if "```" in text:
                start = text.find("```")
                end = text.rfind("```")
                text = text[start:end]
                text = text[text.find("\n") + 1:].strip()

            products = json.loads(text)
            if isinstance(products, dict):
                products = [products]

            print(f"    Page {page_num + 1}: {len(products)} product(s) found")
            return products

        except json.JSONDecodeError as e:
            print(f"    Page {page_num + 1} attempt {attempt + 1}: JSON parse error ({e})")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return []
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower() or "resource_exhausted" in err.lower():
                wait = 30 * (attempt + 1)
                print(f"    Rate limit — waiting {wait}s …")
                time.sleep(wait)
            else:
                print(f"    Page {page_num + 1} attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                else:
                    return []
    return []


def extract_via_file_api(client: genai.Client, pdf_path: str) -> list[dict]:
    """Upload PDF directly via Gemini File API (fallback when PyMuPDF unavailable)."""
    print("  Uploading PDF to Gemini File API …")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    uploaded = client.files.upload(
        file=io.BytesIO(pdf_bytes),
        config=types.UploadFileConfig(
            mime_type="application/pdf",
            display_name=Path(pdf_path).name,
        ),
    )

    # Poll until processed
    while uploaded.state.name == "PROCESSING":
        time.sleep(5)
        uploaded = client.files.get(name=uploaded.name)

    if uploaded.state.name != "ACTIVE":
        raise RuntimeError(f"File API processing failed: {uploaded.state.name}")

    prompt = (
        EXTRACTION_PROMPT
        + "\n\nNote: This is the full PDF catalogue. Extract ALL products from ALL pages and return one flat JSON array."
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[prompt, types.Part.from_uri(file_uri=uploaded.uri, mime_type="application/pdf")],
        config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=16384),
    )

    # Clean up uploaded file
    try:
        client.files.delete(name=uploaded.name)
    except Exception:
        pass

    text = response.text.strip()
    if "```" in text:
        start = text.find("```")
        end = text.rfind("```")
        text = text[start:end]
        text = text[text.find("\n") + 1:].strip()

    products = json.loads(text)
    if isinstance(products, dict):
        products = [products]
    return products


def _build_record(raw: dict, page_num: int, now: str) -> dict:
    """Normalize raw Gemini output into the full column schema."""
    record = {col: None for col in PRODUCT_COLUMNS}

    # Copy matching fields
    for col in PRODUCT_COLUMNS:
        val = raw.get(col)
        if val is not None and val != "null" and val != "":
            record[col] = str(val)

    # Always override these
    record["product_id"]  = str(uuid.uuid4())
    record["status"]      = STATUS_EXTRACTED
    record["source_page"] = str(page_num + 1)
    record["created_at"]  = now
    record["updated_at"]  = now
    record["haravan_product_id"] = None

    return record


def extract_single_page(client: genai.Client, img_bytes: bytes, page_num: int, total_pages: int, now: str) -> list[dict]:
    """Helper to extract a single page, convert to records, with clean logging."""
    t0 = time.time()
    raw_products = extract_from_image(client, img_bytes, page_num)
    records = [_build_record(p, page_num=page_num, now=now) for p in raw_products]
    elapsed = time.time() - t0
    print(f"  ⚡ [Page {page_num + 1}/{total_pages}] Extracted {len(records)} product(s) in {elapsed:.1f}s", flush=True)
    return records


def extract_from_pdf(pdf_path: str, max_workers: int = MAX_WORKERS, on_page_extracted=None) -> list[dict]:
    """
    Multi-threaded extraction function.
    Processes pages concurrently using ThreadPoolExecutor.
    Calls on_page_extracted(page_num, records) as soon as each page completes.
    Returns complete list of products sorted by page number.
    """
    pdf_path = str(Path(pdf_path).resolve())
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    print(f"\n📄 Extracting from: {pdf_path}", flush=True)
    images = pdf_to_images(pdf_path)
    client = get_client()
    now = datetime.utcnow().isoformat() + "Z"

    if images is None:
        raw_products = extract_via_file_api(client, pdf_path)
        all_products = [_build_record(p, page_num=0, now=now) for p in raw_products]
        if on_page_extracted:
            on_page_extracted(0, all_products)
        return all_products

    total_pages = len(images)
    print(f"🚀 Launching multi-threaded extraction with {max_workers} parallel workers for {total_pages} pages …", flush=True)

    page_results = {}
    completed_count = 0
    lock = threading.Lock()
    start_time = time.time()

    def _worker(page_idx: int, img_b: bytes):
        nonlocal completed_count
        records = extract_single_page(client, img_b, page_idx, total_pages, now)
        with lock:
            page_results[page_idx] = records
            completed_count += 1
            progress = (completed_count / total_pages) * 100
            print(f"  📊 Progress: {completed_count}/{total_pages} pages ({progress:.0f}%) | Total products so far: {sum(len(r) for r in page_results.values())}", flush=True)
        if on_page_extracted and records:
            on_page_extracted(page_idx, records)
        return records

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_worker, i, img) for i, img in enumerate(images)]
        concurrent.futures.wait(futures)

    # Combine sorted by page number
    all_products = []
    for i in range(total_pages):
        all_products.extend(page_results.get(i, []))

    total_time = time.time() - start_time
    print(f"\n✅ Multi-threaded extraction complete in {total_time:.1f}s!", flush=True)
    print(f"   Total pages   : {total_pages}", flush=True)
    print(f"   Total products: {len(all_products)}", flush=True)
    return all_products
