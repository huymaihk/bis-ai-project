"""
Raw Product Image Store & PDF Candidate Extraction for BIS Textile.
Handles:
1. Extracting candidate images from PDF pages prioritized by SKU match.
2. Batch/paginated extraction of all images across PDF catalogues.
3. Page/region rendering for scanned PDFs.
4. Deduplicating by SHA256 and saving raw images as {SKU}_1.png, {SKU}_2.png...
5. Calibration memory (accepted vs rejected candidates) for ranking improvements.
6. Managing unassigned candidate image pool.
"""
from __future__ import annotations
import re
import io
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import pymupdf
from persistent_memory import atomic_json, clean

def natural_sort_key(filename: str) -> list[int | str]:
    """Sort filenames naturally (e.g. 03026A_1.png, 03026A_2.png, 03026A_10.png)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', filename)]

from completed_images import matches_sku_exact

def get_calibration_memory(memory, sku: str) -> dict[str, str]:
    """Retrieve calibration feedback memory for SKU: sha256 -> 'ACCEPTED' | 'REJECTED'."""
    if memory is None:
        return {}
    decisions = {}
    try:
        events = sorted(memory.events(), key=lambda e: (e.get("created_at", ""), e.get("id", "")))
        for ev in events:
            if ev.get("key") == f"image-calibration:{sku}":
                try:
                    data = json.loads(ev.get("content", "{}"))
                    for h in data.get("reset_hashes", []):
                        decisions.pop(h, None)
                    for h in data.get("accepted_hashes", []):
                        decisions[h] = "ACCEPTED"
                    for h in data.get("rejected_hashes", []):
                        decisions[h] = "REJECTED"
                except Exception:
                    pass
    except Exception:
        pass
    return decisions

def extract_sku_page_candidates(pdf_path: str | Path, sku: str, memory=None) -> list[dict]:
    """
    Extract candidate images prioritizing pages containing the exact SKU.
    Applies calibration memory scoring.
    """
    sku = str(sku).strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", sku):
        raise ValueError("SKU không hợp lệ để đặt tên ảnh")
    pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(sku) + r"(?![A-Za-z0-9])", re.I)
    calibration = get_calibration_memory(memory, sku)
    results = []

    with pymupdf.open(str(pdf_path)) as doc:
        for page in doc:
            page_text = page.get_text()
            if not pattern.search(page_text):
                continue
            seen = set()
            for info in page.get_image_info(xrefs=True):
                if len(results) >= 48: return results
                xref = info.get("xref", 0)
                if not xref or xref in seen:
                    continue
                seen.add(xref)
                try:
                    data = doc.extract_image(xref)
                except Exception:
                    continue
                smask = next((x[1] for x in page.get_images(full=True) if x[0] == xref), 0)
                if smask:
                    try:
                        pix = pymupdf.Pixmap(pymupdf.Pixmap(doc, xref), pymupdf.Pixmap(doc, smask))
                        data.update(image=pix.tobytes("png"), ext="png")
                    except Exception:
                        pass
                
                img_bytes = data["image"]
                sha256 = hashlib.sha256(img_bytes).hexdigest()
                cal_status = calibration.get(sha256, "UNKNOWN")
                score = 50
                if cal_status == "ACCEPTED":
                    score += 40
                elif cal_status == "REJECTED":
                    score -= 40

                results.append({
                    "page": page.number + 1,
                    "xref": xref,
                    "bbox": list(info.get("bbox", [0, 0, 0, 0])),
                    "width": data.get("width", 0),
                    "height": data.get("height", 0),
                    "ext": data.get("ext", "png"),
                    "source_file": str(pdf_path),
                    "image_bytes": img_bytes,
                    "sha256": sha256,
                    "sku": sku,
                    "calibration_status": cal_status,
                    "score": score,
                    "kind": "pdf_page_match",
                    "status": "NEEDS_REVIEW"
                })

    # Sort candidates by score descending, then by page and area
    results.sort(key=lambda r: (-r["score"], r["page"], -(r["width"] * r["height"])))
    return results

def extract_pdf_batch(pdf_path: str | Path, start_page: int = 1, end_page: Optional[int] = None, max_images: int = 60, image_offset: int = 0) -> dict:
    """
    Extract embedded images across a range of pages in the PDF with pagination.
    Returns: {total_pages, start_page, end_page, images: [...]}
    """
    start_page = int(start_page)
    if start_page < 1 or not 1 <= max_images <= 60: raise ValueError('Phạm vi trích ảnh không hợp lệ')
    images = []
    next_page = None
    next_offset = 0
    with pymupdf.open(str(pdf_path)) as doc:
        total_pages = len(doc)
        if start_page > total_pages: raise ValueError('Trang bắt đầu vượt tài liệu')
        if end_page is not None and (end_page < start_page or end_page > total_pages): raise ValueError('Trang kết thúc không hợp lệ')
        if end_page is None:
            target_end = min(total_pages, start_page + 9) # Default 10 pages per batch
        else:
            target_end = min(int(end_page), start_page + 9)

        for page_idx in range(start_page - 1, target_end):
            page = doc[page_idx]
            seen = set()
            for position, info in enumerate(page.get_image_info(xrefs=True)):
                if page_idx == start_page - 1 and position < image_offset: continue
                if len(images) >= max_images:
                    next_page, next_offset = page_idx + 1, position
                    break
                xref = info.get("xref", 0)
                if not xref or xref in seen:
                    continue
                seen.add(xref)
                try:
                    data = doc.extract_image(xref)
                except Exception:
                    continue
                smask = next((x[1] for x in page.get_images(full=True) if x[0] == xref), 0)
                if smask:
                    try:
                        pix = pymupdf.Pixmap(pymupdf.Pixmap(doc, xref), pymupdf.Pixmap(doc, smask))
                        data.update(image=pix.tobytes("png"), ext="png")
                    except Exception:
                        pass
                
                img_bytes = data["image"]
                sha256 = hashlib.sha256(img_bytes).hexdigest()
                images.append({
                    "page": page_idx + 1,
                    "xref": xref,
                    "bbox": list(info.get("bbox", [0, 0, 0, 0])),
                    "width": data.get("width", 0),
                    "height": data.get("height", 0),
                    "ext": data.get("ext", "png"),
                    "source_file": str(pdf_path),
                    "image_bytes": img_bytes,
                    "sha256": sha256,
                    "kind": "pdf_batch",
                    "status": "UNASSIGNED"
                })

            if next_page is not None: break
        if next_page is None and target_end < total_pages:
            next_page = target_end + 1

    return {
        "next_page": next_page,
        "next_offset": next_offset,
        "total_pages": total_pages,
        "start_page": start_page,
        "end_page": target_end,
        "images": images
    }

def render_scanned_region(pdf_path: str | Path, page_number: int, region: Tuple[float, float, float, float] = (0, 0, 100, 100), dpi: int = 150) -> bytes:
    """
    Render a page or crop region for scanned PDFs or vector catalogues without isolated images.
    region is (x0, y0, x1, y1) in percentages (0 to 100).
    """
    x0, y0, x1, y1 = region
    if not (0 <= x0 < x1 <= 100 and 0 <= y0 < y1 <= 100):
        raise ValueError("Tọa độ vùng cắt phải từ 0% đến 100% và x0 < x1, y0 < y1")
    with pymupdf.open(str(pdf_path)) as doc:
        if page_number < 1 or page_number > len(doc):
            raise ValueError(f"Số trang {page_number} vượt quá phạm vi tài liệu (1..{len(doc)})")
        page = doc[page_number - 1]
        rect = page.rect
        crop_rect = pymupdf.Rect(
            rect.x0 + rect.width * (x0 / 100.0),
            rect.y0 + rect.height * (y0 / 100.0),
            rect.x0 + rect.width * (x1 / 100.0),
            rect.y0 + rect.height * (y1 / 100.0)
        )
        if crop_rect.width * crop_rect.height * (dpi / 72.0)**2 > 20_000_000: raise ValueError('Vùng ảnh quá lớn; chọn vùng nhỏ hơn')
        matrix = pymupdf.Matrix(dpi / 72.0, dpi / 72.0)
        pix = page.get_pixmap(matrix=matrix, clip=crop_rect)
        return pix.tobytes("png")

def save_raw_product_images(
    root: Path,
    sku: str,
    selected_items: list[dict],
    all_presented_items: Optional[list[dict]] = None,
    user: str = "operator",
    memory = None
) -> dict:
    """
    Save confirmed raw candidate images to Google_Drive_Storage/4_Product_Images/raw/.
    Rules:
    - Naming convention: {SKU}_1.png, {SKU}_2.png...
    - Preserves embedded quality.
    - Anti-collision & deduplication via SHA256 (no identical hash saved twice).
    - Writes metadata to raw_manifest.json.
    - Updates calibration memory (accepted vs rejected candidates).
    """
    sku = str(sku).strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", sku):
        raise ValueError("SKU không hợp lệ để đặt tên ảnh")
    if not selected_items:
        raise ValueError("Chưa chọn ảnh nào để lưu")

    raw_dir = (root / "Google_Drive_Storage" / "4_Product_Images" / "raw").resolve()
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = raw_dir / "raw_manifest.json"

    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError('Không đọc được hồ sơ ảnh; giữ nguyên dữ liệu và kiểm tra lại') from exc

    # Scan existing files for this SKU to find next index & existing hashes
    existing_files = list(raw_dir.glob(f"{sku}_*.png")) + list(raw_dir.glob(f"{sku}_*.jpg"))
    existing_hashes = {}
    used_indices = set()
    for f in existing_files:
        m = re.match(rf"^{re.escape(sku)}_(\d+)\.", f.name)
        if m:
            idx = int(m.group(1))
            used_indices.add(idx)
            try:
                h = hashlib.sha256(f.read_bytes()).hexdigest()
                existing_hashes[h] = f.name
            except Exception:
                pass

    saved_records = []
    accepted_hashes = []

    next_idx = 1
    for item in selected_items:
        img_bytes = item.get("image_bytes")
        if not img_bytes:
            continue
        source_sha256 = hashlib.sha256(img_bytes).hexdigest()
        from PIL import Image
        with Image.open(io.BytesIO(img_bytes)) as image:
            if image.width * image.height > 40_000_000:
                raise ValueError('Ảnh vượt giới hạn 40 megapixel')
            output = io.BytesIO()
            image.convert('RGBA' if 'A' in image.getbands() else 'RGB').save(output, format='PNG')
            img_bytes = output.getvalue()
        sha256 = hashlib.sha256(img_bytes).hexdigest()
        accepted_hashes.append(source_sha256)

        # Chống trùng: đã tồn tại file cùng hash cho SKU này
        if sha256 in existing_hashes:
            filename = existing_hashes[sha256]
            saved_records.append({
                "filename": filename,
                "sku": sku,
                "sha256": sha256,
                "deduplicated": True,
                "message": f"Ảnh đã tồn tại dưới tên {filename} (chống trùng SHA256)"
            })
            continue

        # Find next available index
        while next_idx in used_indices:
            next_idx += 1
        used_indices.add(next_idx)

        filename = f"{sku}_{next_idx}.png"
        target_path = raw_dir / filename
        with target_path.open('xb') as handle:
            handle.write(img_bytes)
        existing_hashes[sha256] = filename

        record = {
            "filename": filename,
            "sku": sku,
            "sha256": sha256,
            "width": item.get("width"),
            "height": item.get("height"),
            "ext": "png",
            "source_sha256": source_sha256,
            "source_file": str(item.get("source_file", "")),
            "source_page": item.get("page"),
            "xref": item.get("xref"),
            "bbox": item.get("bbox"),
            "confirmed_by": user,
            "confirmed_at": datetime.now(timezone.utc).isoformat(),
            "deduplicated": False
        }
        manifest[filename] = record
        saved_records.append(record)

    atomic_json(manifest_path, manifest)

    # Calibration memory recording
    if memory is not None:
        rejected_hashes = []
        cal_payload = {
            "sku": sku,
            "accepted_hashes": accepted_hashes,
            "rejected_hashes": rejected_hashes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "description": "Bộ nhớ hiệu chỉnh (calibration memory) phân loại ảnh ứng viên, không phải huấn luyện lại model."
        }
        try:
            memory.append(
                kind="correction",
                content=json.dumps(cal_payload, ensure_ascii=False),
                key=f"image-calibration:{sku}",
                source="User confirmed raw images (calibration memory, not model fine-tuning)"
            )
        except Exception:
            pass

    return {
        "status": "SAVED",
        "saved_count": len(saved_records),
        "records": saved_records
    }

def list_raw_images(root: Path, sku: Optional[str] = None) -> list[dict]:
    """List raw product images from raw_manifest.json and directory, naturally sorted."""
    raw_dir = (root / "Google_Drive_Storage" / "4_Product_Images" / "raw").resolve()
    manifest_path = raw_dir / "raw_manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}

    results = []
    if raw_dir.exists():
        for f in raw_dir.glob("*.png"):
            if sku and not matches_sku_exact(f.name, sku):
                continue
            meta = manifest.get(f.name, {})
            results.append({
                "filename": f.name,
                "sku": meta.get("sku") or (f.name.split("_")[0] if "_" in f.name else sku or ""),
                "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                "width": meta.get("width"),
                "height": meta.get("height"),
                "source_file": meta.get("source_file"),
                "source_page": meta.get("source_page"),
                "confirmed_at": meta.get("confirmed_at"),
                "size": f.stat().st_size
            })

    results.sort(key=lambda r: natural_sort_key(r["filename"]))
    return results
