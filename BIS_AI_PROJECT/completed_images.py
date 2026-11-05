"""
Completed Composites & Flow AI Integration for BIS Textile.
Handles:
1. Scanning Google_Drive_Storage/6_Final_Composites/ with strict SKU boundary regex.
2. Natural numerical sorting (1, 2, ..., 10).
3. Preserving legacy formats with dedicated badges.
4. Tampering & SHA256 change detection for confirmed image sets.
5. Confirming image set (multi-select, primary image, sequence, SHA256 recording).
6. Exporting Flow AI semi-automated packages (raw images + BIS backdrop + precise composition prompt).
"""
from __future__ import annotations
import os
import re
import io
import json
import zipfile
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any

from persistent_memory import atomic_json

def natural_sort_key(filename: str) -> list[int | str]:
    """Sort filenames naturally (e.g. 03026A_1.png, 03026A_2.png, 03026A_10.png)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', filename)]

def matches_sku_exact(filename: str, sku: str) -> bool:
    """
    Exact SKU boundary matching.
    SKU 03026A matches:
      03026A_1.png, 03026A_2.jpg, 03026A_10.png, 03026A_final.jpg, 03026A.png, 03026A_approved_...png
    SKU 03026A does NOT match:
      03026AB_1.png, 03026A1.png, 03026B_1.png
    """
    pattern = re.compile(r'^' + re.escape(sku) + r'(?:_[1-9]\d*|_final|_approved_[a-f0-9]+)?\.(?:png|jpe?g|webp)$', re.I)
    return bool(pattern.match(filename))

def safe_image_path(folder, filename, sku=None):
    if not isinstance(filename, str) or not filename or '/' in filename or chr(92) in filename:
        raise ValueError('Tên ảnh không hợp lệ')
    path = (folder / filename).resolve()
    if path.parent != folder.resolve() or path.suffix.lower() not in {'.png','.jpg','.jpeg','.webp'}:
        raise ValueError('Ảnh nằm ngoài thư mục cho phép')
    if sku is not None and not matches_sku_exact(filename, sku):
        raise ValueError('Ảnh không thuộc SKU đang chọn')
    if not path.is_file():
        raise ValueError('Ảnh không còn tồn tại; quét lại thư mục')
    return path


def is_legacy_filename(filename: str, sku: str) -> bool:
    """Return True if image follows an older naming convention like _final.jpg or no index."""
    lower = filename.lower()
    if "_final" in lower or "_approved_" in lower:
        return True
    # If it's just {sku}.ext without _1, _2
    if re.match(rf'^{re.escape(sku)}\.[a-zA-Z0-9]+$', filename, re.I):
        return True
    return False

def scan_completed_composites(root: Path, sku: Optional[str] = None) -> list[dict]:
    """
    Scan Google_Drive_Storage/6_Final_Composites/ matching exact SKU boundary.
    Checks confirmed status and detects SHA256 tampering.
    """
    final_dir = (root / "Google_Drive_Storage" / "6_Final_Composites").resolve()
    manifest_path = (root / "Google_Drive_Storage" / "image_review_manifest.json").resolve()
    
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}

    allowed_exts = {".png", ".jpg", ".jpeg", ".webp"}
    results = []

    if not final_dir.exists():
        return []

    for file_path in final_dir.iterdir():
        if not file_path.is_file() or file_path.suffix.lower() not in allowed_exts:
            continue
        
        filename = file_path.name
        if sku and not matches_sku_exact(filename, sku):
            continue

        if file_path.resolve().parent != final_dir: continue
        file_bytes = file_path.read_bytes()
        current_sha256 = hashlib.sha256(file_bytes).hexdigest()
        is_legacy = is_legacy_filename(filename, sku or "")

        # Check manifest for confirmation & tampering
        sku_manifest = manifest.get(sku, {}) if sku else {}
        confirmed_set = sku_manifest.get("images", [])
        
        # Check if this file was part of confirmed set
        matched_confirmed = None
        for item in confirmed_set:
            if item.get("filename") == filename:
                matched_confirmed = item
                break

        # Also support older manifest format with "approved_sha256" and "final_image"
        if not matched_confirmed and sku_manifest.get("status") == "APPROVED":
            old_final = sku_manifest.get("final_image", "")
            if old_final.replace(chr(92), '/').split('/')[-1] == filename:
                matched_confirmed = {
                    "filename": filename,
                    "sha256": sku_manifest.get("approved_sha256", ""),
                    "is_primary": True,
                    "order": 1
                }

        is_confirmed = False
        hash_mismatch = False
        is_primary = False
        order_num = 999

        if matched_confirmed:
            is_confirmed = True
            is_primary = matched_confirmed.get("is_primary", False)
            order_num = matched_confirmed.get("order", 1)
            stored_sha256 = matched_confirmed.get("sha256", "")
            if not stored_sha256 or stored_sha256 != current_sha256:
                hash_mismatch = True
                is_confirmed = False

        results.append({
            "filename": filename,
            "path": f"Google_Drive_Storage/6_Final_Composites/{filename}",
            "sha256": current_sha256,
            "size": len(file_bytes),
            "is_legacy": is_legacy,
            "legacy_label": f"Ảnh thành phẩm cũ ({filename})" if is_legacy else None,
            "is_confirmed": is_confirmed,
            "is_primary": is_primary,
            "order": order_num,
            "hash_mismatch": hash_mismatch,
            "warning": "Tập tin đã bị thay đổi trên đĩa sau khi xác nhận! Cần đối chiếu lại." if hash_mismatch else None,
            "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc).isoformat()
        })

    # Sort naturally: primary first or by order if confirmed, then by natural sort key
    results.sort(key=lambda r: (0 if r["is_primary"] else 1, r["order"], natural_sort_key(r["filename"])))
    return results

def confirm_completed_image_set(
    root: Path,
    sku: str,
    items: list[dict],
    primary_filename: str,
    user: str = "operator",
    memory = None
) -> dict:
    """
    Confirm approved completed image set for SKU.
    Validates files and SHA256 hashes on disk.
    Updates image_review_manifest.json and MemoryStore.
    """
    sku = str(sku).strip()
    if not sku:
        raise ValueError("SKU không được để trống")
    if not items:
        raise ValueError("Chưa chọn ảnh nào trong bộ ảnh thành phẩm")

    final_dir = (root / "Google_Drive_Storage" / "6_Final_Composites").resolve()
    manifest_path = (root / "Google_Drive_Storage" / "image_review_manifest.json").resolve()

    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError('Không đọc được hồ sơ ảnh; giữ nguyên dữ liệu và kiểm tra lại') from exc

    if len(items) > 50 or len({i.get('filename') for i in items}) != len(items):
        raise ValueError('Bộ ảnh bị trùng hoặc vượt 50 ảnh')
    if primary_filename not in {i.get('filename') for i in items}:
        raise ValueError('Ảnh chính phải nằm trong bộ ảnh được chọn')
    validated_images = []
    primary_found = False

    for idx, item in enumerate(items):
        filename = item.get("filename")
        if not filename:
            continue
        file_path = safe_image_path(final_dir, filename, sku)
        if not file_path.is_file():
            raise FileNotFoundError(f"Không tìm thấy file {filename} trong 6_Final_Composites/")
        
        sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if not item.get('sha256') or item['sha256'] != sha256:
            raise ValueError('Ảnh đã thay đổi từ lần xem trước; quét và đối chiếu lại')
        is_primary = (filename == primary_filename)
        if is_primary:
            primary_found = True

        validated_images.append({
            "filename": filename,
            "sha256": sha256,
            "order": idx + 1,
            "is_primary": is_primary,
            "path": f"Google_Drive_Storage/6_Final_Composites/{filename}"
        })

    if not primary_found and validated_images:
        validated_images[0]["is_primary"] = True
        primary_filename = validated_images[0]["filename"]

    confirmed_payload = {
        "sku": sku,
        "status": "APPROVED_SET",
        "primary_image": primary_filename,
        "confirmed_at": datetime.now(timezone.utc).isoformat(),
        "confirmed_by": user,
        "images": validated_images
    }

    # Separate review set does not grant existing shop publication approval.
    manifest[sku] = confirmed_payload
    atomic_json(manifest_path, manifest)

    if memory is not None:
        try:
            memory.append(
                kind="update",
                content=json.dumps(confirmed_payload, ensure_ascii=False),
                key=f"image-approved-set:{sku}",
                source="User confirmed completed composite image set (SHA256 verified)"
            )
        except Exception:
            pass

    return confirmed_payload

def export_flow_ai_package(
    root: Path,
    sku: str,
    raw_filenames: Optional[list[str]] = None,
    background_filename: str = "BIS_BACKDROP_1254.png"
) -> bytes:
    """
    Export semi-automated bridge package for Flow AI.
    Contains:
    1. Raw product images from Google_Drive_Storage/4_Product_Images/raw/
    2. Official BIS studio backdrop
    3. FLOW_AI_PROMPT.txt with rigorous truthfulness and dimension preservation rules
    4. FLOW_AI_METADATA.json with SKU and file checksums
    """
    raw_dir = (root / "Google_Drive_Storage" / "4_Product_Images" / "raw").resolve()
    bg_dir = (root / "Google_Drive_Storage" / "5_Studio_Backgrounds").resolve()

    bg_path = safe_image_path(bg_dir, background_filename)
    if not bg_path.exists():
        # Fallback to any BIS_BACKDROP in studio backgrounds or 4_Product_Images
        candidates = [
            bg_dir / "BIS_BACKDROP_1254.png",
            bg_dir / "BIS_BACKGROUND.png",
            root / "Google_Drive_Storage" / "4_Product_Images" / "BIS_BACKGROUND.png"
        ]
        for c in candidates:
            if c.exists():
                bg_path = c
                break

    # Determine raw files
    raw_paths = []
    if raw_filenames:
        for fname in raw_filenames:
            raw_paths.append(safe_image_path(raw_dir, fname, sku))
    if not raw_paths:
        # Auto-pick all raw files for this SKU
        if raw_dir.exists():
            for p in raw_dir.iterdir():
                if matches_sku_exact(p.name, sku):
                    raw_paths.append(safe_image_path(raw_dir, p.name, sku))
    raw_paths.sort(key=lambda p: natural_sort_key(p.name))

    if not raw_paths:
        raise ValueError(f"Chưa có ảnh thô nào cho SKU {sku} trong thư mục raw/")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        metadata = {
            "sku": sku,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "target_folder": "Google_Drive_Storage/6_Final_Composites/",
            "naming_convention": f"{sku}_1.png, {sku}_2.png...",
            "raw_images": []
        }

        # Write raw images
        for idx, rp in enumerate(raw_paths):
            arcname = f"01_RAW_{rp.name}"
            z.write(rp, arcname)
            metadata["raw_images"].append({
                "original_name": rp.name,
                "sha256": hashlib.sha256(rp.read_bytes()).hexdigest(),
                "suggested_final_name": rp.name
            })

        # Write background
        if bg_path and bg_path.exists():
            z.write(bg_path, f"02_BACKDROP_{bg_path.name}")
            metadata["backdrop"] = {
                "name": bg_path.name,
                "sha256": hashlib.sha256(bg_path.read_bytes()).hexdigest()
            }

        # Write prompt instructions
        prompt_text = f"""======================================================================
FLOW AI PRODUCT STUDIO COMPOSITION INSTRUCTIONS
SKU: {sku}
======================================================================

You are composing commercial studio product photographs for BIS Textile.
Follow these mandatory product integrity rules:

1. COMPOSITION & PLACEMENT:
   - Place the product cleanly onto the provided official BIS Backdrop (02_BACKDROP_*.png).
   - The product must stand firmly on the ground plane (studio floor) with realistic contact shadows.
   - PRODUCT SIZE: The product must fill approximately 70% to 80% of the frame. Do NOT shrink it into a tiny object in the center.

2. LIGHTING & COLOR:
   - Apply balanced, neutral commercial studio lighting.
   - Maintain true-to-life materials and colors (metal, plastic, textiles, rubber).
   - Clean background artifacts while keeping crisp product edges.

3. ZERO HALLUCINATION & DETAIL PRESERVATION (CRITICAL):
   - Strictly preserve the exact mechanical and physical geometry of the product.
   - Keep all screws, dials, switches, slots, dividing lines, and graduation marks.
   - DO NOT invent, hallucinate, or alter any text, numbers, model codes, scale markings, or logos.
   - If text on the raw image is partially unclear, DO NOT attempt to guess or invent new letters.

4. EXPORT & NAMING:
   - Save high-resolution outputs (minimum 1254 x 1254 px).
   - Name completed files:
     {sku}_1.png
     {sku}_2.png (if multiple angles)
   - Place completed images into:
     Google_Drive_Storage/6_Final_Composites/
"""
        z.writestr("FLOW_AI_PROMPT.txt", prompt_text.strip())
        z.writestr("FLOW_AI_METADATA.json", json.dumps(metadata, ensure_ascii=False, indent=2))
        z.writestr("README_FLOW_AI.txt", "1. Open Flow AI / web image editor.\n2. Upload 01_RAW image(s) and 02_BACKDROP.\n3. Paste prompt from FLOW_AI_PROMPT.txt.\n4. Export completed image(s) as " + sku + "_1.png into Google_Drive_Storage/6_Final_Composites/.\n5. In BIS, open tab 'Hình ảnh hoàn thiện' and click 'Quét ảnh hoàn thiện' to review and confirm.")

    return buf.getvalue()
