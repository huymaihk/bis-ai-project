"""
BIS Textile AI - Flow 2D Studio Generator
=========================================
Quy trình tự động hóa (Automated Background Flow):
- Nhận diện phôi nền chính hãng BIS Textile: BIS_BACKGROUND.png (tường đứng + sàn phối cảnh)
- Tách nền sản phẩm thông minh, giữ nguyên 100% hình khối 2D thực tế (không méo 3D, không ảo)
- Cân chỉnh kích thước chuẩn catalogue thương mại (cao ~580px, chiếm 55-60% khung hình)
- Đặt sản phẩm đứng vững chãi trên sàn (ground_y = 800)
- Đổ bóng vật lý 2 lớp chân thực (Ambient Occlusion + Soft Shadow) như ảnh chụp studio thực tế
- Tự động lưu thẳng vào thư mục Google Drive:
  + Google_Drive_Storage/6_Final_Composites/{sku}_final.jpg
  + Google_Drive_Storage/5_Draft_Previews/{sku}_preview.jpg
- Tự động đồng bộ manifest duyệt ảnh (image_review_manifest.json)
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Optional, Dict, List

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw

PROJECT_DIR = Path(__file__).parent.resolve()
STORAGE_DIR = PROJECT_DIR / "Google_Drive_Storage"
PRODUCT_DIR = STORAGE_DIR / "4_Product_Images"
BG_DIR = STORAGE_DIR / "5_Studio_Backgrounds"
PREVIEW_DIR = STORAGE_DIR / "5_Draft_Previews"
FINAL_DIR = STORAGE_DIR / "6_Final_Composites"
MANIFEST_PATH = STORAGE_DIR / "image_review_manifest.json"

for d in [STORAGE_DIR, PRODUCT_DIR, BG_DIR, PREVIEW_DIR, FINAL_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# Kích thước tiêu chuẩn vàng (Golden Benchmark từ 6_Final_Composites)
CANVAS_SIZE = (1254, 1254)
CANVAS_W = 1254
CANVAS_H = 1254


def find_bis_backdrop() -> Path:
    """Tìm phôi nền BIS Textile đạt chuẩn thương hiệu 1254x1254 (hoặc 1024x1024)."""
    candidates = [
        BG_DIR / "BIS_BACKDROP_1254.png",
        PRODUCT_DIR / "BIS_BACKDROP_1254.png",
        PROJECT_DIR / "BIS_BACKDROP_1254.png",
        BG_DIR / "BIS_BACKGROUND.png",
        PRODUCT_DIR / "BIS_BACKGROUND.png",
        PROJECT_DIR / "BIS_BACKGROUND.png",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("Không tìm thấy file BIS_BACKDROP_1254.png hoặc BIS_BACKGROUND.png trong thư mục Studio Backgrounds.")


def clean_and_cutout_product(prod_img: Image.Image) -> Image.Image:
    """
    Tách nền sản phẩm quang học thông minh (Optical Matting):
    - Cắt viền đen scan nếu có.
    - Dùng FloodFill đa điểm từ các góc viền để loại bỏ nền trắng/xám bên ngoài.
    - Tự động feathering biên dạng 1.5px để triệt tiêu răng cưa viền trắng.
    - Bảo toàn 100% chi tiết cơ khí, rãnh xẻ, ốc vít, font chữ dập chìm và logo.
    """
    im = prod_img.convert("RGBA")
    arr = np.array(im)
    h, w = arr.shape[:2]

    # 1. Cắt viền đen scan
    if arr[:5, :, :3].mean() < 30 or arr[:, :5, :3].mean() < 30:
        mask = (arr[:, :, 0] > 25) | (arr[:, :, 1] > 25) | (arr[:, :, 2] > 25)
        rows = np.where(mask.any(axis=1))[0]
        cols = np.where(mask.any(axis=0))[0]
        if len(rows) and len(cols):
            im = im.crop((cols[0], rows[0], cols[-1] + 1, rows[-1] + 1))
            arr = np.array(im)
            h, w = arr.shape[:2]

    # 2. Xử lý nền trắng/sáng bên ngoài
    bgr = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    
    # Kiểm tra màu nền ở 4 dải viền ngoài cùng
    edge_strip = np.concatenate([gray[:12, :].flatten(), gray[-12:, :].flatten(), gray[:, :12].flatten(), gray[:, -12:].flatten()])
    bg_median = float(np.median(edge_strip))

    if (arr[:, :, 3] < 250).sum() < 100 and bg_median > 180:
        flood_mask = np.zeros((h + 2, w + 2), np.uint8)
        seeds = [
            (0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
            (0, h // 2), (w - 1, h // 2), (w // 2, 0), (w // 2, h - 1),
            (2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)
        ]
        diff_tol = max(16, int(abs(bg_median - 255) + 18))
        for sx, sy in seeds:
            if gray[sy, sx] > (bg_median - diff_tol):
                cv2.floodFill(
                    bgr.copy(), flood_mask, (sx, sy),
                    (0, 0, 0), (diff_tol, diff_tol, diff_tol), (diff_tol, diff_tol, diff_tol),
                    flags=4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8)
                )
        
        ext_bg_mask = (flood_mask[1:h+1, 1:w+1] == 255)
        alpha = np.where(ext_bg_mask, 0, 255).astype(np.uint8)

        # Lấp các lỗ rỗng nhỏ bên trong chi tiết kim loại/chữ dập chìm
        contours, _ = cv2.findContours(alpha, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        solid_mask = np.zeros_like(alpha)
        for cnt in contours:
            if cv2.contourArea(cnt) > 800:
                cv2.drawContours(solid_mask, [cnt], -1, 255, -1)
        
        # Làm mịn viền (Antialiasing feathering 1.5px)
        feathered = cv2.GaussianBlur(solid_mask, (5, 5), sigmaX=1.5)
        arr[:, :, 3] = feathered
        im = Image.fromarray(arr, mode="RGBA")
        bbox = im.getbbox()
        if bbox:
            im = im.crop(bbox)

    return im


def enhance_product_sharpness(prod_rgba: Image.Image, boost: float = 1.6) -> Image.Image:
    """
    Thuật toán làm nét quang học không biến dạng (Zero-Hallucination Optical Sharpening):
    - LAB CLAHE trên kênh Luminance (L): Tăng tương phản vi cấu trúc và khắc nổi chữ 2.0 KG / logo AATCC.
    - Bilateral Filter: Khử nhiễu cảm biến hạt mà không làm mờ cạnh viền sắc nét.
    - High-Pass Unsharp Masking: Nâng độ nét tần số cao của chi tiết máy móc.
    - Tuyệt đối bảo toàn 100% hình khối, vị trí chữ và logo nguyên bản.
    """
    if boost <= 1.0:
        return prod_rgba
    
    rgba = prod_rgba.convert("RGBA")
    r, g, b, a = rgba.split()
    rgb = Image.merge("RGB", (r, g, b))
    bgr = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)

    # 1. LAB CLAHE trên kênh Luminance
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l_chan, a_chan, b_chan = cv2.split(lab)
    clip_lim = float(np.clip(1.5 + (boost - 1.0) * 0.8, 1.5, 2.5))
    clahe = cv2.createCLAHE(clipLimit=clip_lim, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l_chan)
    lab_enhanced = cv2.merge([l_enhanced, a_chan, b_chan])
    bgr_clahe = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

    # 2. Khử nhiễu bảo toàn cạnh sắc
    denoised = cv2.bilateralFilter(bgr_clahe, d=5, sigmaColor=25, sigmaSpace=25)

    # 3. High-Pass Unsharp Masking
    gaussian = cv2.GaussianBlur(denoised, (0, 0), sigmaX=2.0)
    weight = float(np.clip(1.0 + (boost - 1.0) * 1.5, 1.2, 2.6))
    unsharp = cv2.addWeighted(denoised, weight, gaussian, -(weight - 1.0), 0)

    # 4. Detail enhance
    try:
        enhanced_cv = cv2.detailEnhance(unsharp, sigma_s=8, sigma_r=0.15)
    except Exception:
        enhanced_cv = unsharp

    rgb_enh = cv2.cvtColor(enhanced_cv, cv2.COLOR_BGR2RGB)
    pil_enh = Image.fromarray(rgb_enh)
    pil_enh = ImageEnhance.Contrast(pil_enh).enhance(1.05)
    pil_enh = ImageEnhance.Sharpness(pil_enh).enhance(1.15)

    res_rgba = pil_enh.convert("RGBA")
    res_rgba.putalpha(a)
    return res_rgba


def apply_2d_contact_shadow(
    backdrop: Image.Image,
    prod_rgba: Image.Image,
    pos_x: int,
    pos_y: int,
    shadow_density: float = 0.85,
    enable_reflection: bool = True
) -> Image.Image:
    """
    Tạo bóng tiếp xúc chân đế chân thực chuẩn ảnh chụp studio:
    - Lớp 1 (Ambient Occlusion): Dải elip đậm dẹp sát chân đáy (opacity ~85-90%).
    - Lớp 2 (Soft Drop Shadow): Bóng tỏa mềm nhẹ phía dưới và hơi tràn sang 2 bên.
    - Lớp 3 (Floor Reflection nhẹ): Phản chiếu mờ 18% chân đế xuống mặt sàn mica/studio.
    """
    canvas_w, canvas_h = backdrop.size
    prod_w, prod_h = prod_rgba.size
    ground_y = pos_y + prod_h

    comp = backdrop.copy().convert("RGBA")

    # 1. Subtle Floor Reflection (Phản xạ sàn bóng mờ)
    if enable_reflection:
        refl_h = max(int(prod_h * 0.16), 14)
        bottom_part = prod_rgba.crop((0, prod_h - refl_h, prod_w, prod_h))
        flipped = bottom_part.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

        grad_mask = Image.new("L", (prod_w, refl_h), 0)
        g_draw = ImageDraw.Draw(grad_mask)
        for y in range(refl_h):
            val = int(32 * (1.0 - y / refl_h))
            g_draw.line([(0, y), (prod_w, y)], fill=val)

        f_r, f_g, f_b, f_a = flipped.split()
        comb_a = Image.fromarray((np.array(f_a).astype(float) * np.array(grad_mask).astype(float) / 255.0).astype(np.uint8))
        flipped.putalpha(comb_a)
        flipped = flipped.filter(ImageFilter.GaussianBlur(1.8))

        refl_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        refl_layer.paste(flipped, (pos_x, ground_y))
        comp = Image.alpha_composite(comp, refl_layer)

    # 2. Soft Drop Shadow (Bóng tỏa mềm)
    soft_shadow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(soft_shadow)
    soft_opacity = int(70 * float(shadow_density))
    soft_w_expand = int(prod_w * 0.12)
    soft_h = max(int(prod_h * 0.08), 24)
    soft_box = [
        pos_x - soft_w_expand,
        ground_y - int(soft_h * 0.25),
        pos_x + prod_w + soft_w_expand,
        ground_y + int(soft_h * 1.15)
    ]
    s_draw.ellipse(soft_box, fill=(20, 20, 25, soft_opacity))
    soft_shadow = soft_shadow.filter(ImageFilter.GaussianBlur(16))
    comp = Image.alpha_composite(comp, soft_shadow)

    # 3. Ambient Occlusion (Bóng tiếp xúc chân đế sát sàn)
    ao_shadow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    ao_draw = ImageDraw.Draw(ao_shadow)
    ao_opacity = int(210 * float(shadow_density))
    ao_h = max(int(prod_h * 0.026), 8)
    ao_box = [
        pos_x + int(prod_w * 0.04),
        ground_y - int(ao_h * 0.5),
        pos_x + prod_w - int(prod_w * 0.04),
        ground_y + int(ao_h * 0.75)
    ]
    ao_draw.ellipse(ao_box, fill=(10, 10, 15, ao_opacity))
    ao_shadow = ao_shadow.filter(ImageFilter.GaussianBlur(3))
    comp = Image.alpha_composite(comp, ao_shadow)

    # 4. Đặt sản phẩm lên trên cùng
    comp.paste(prod_rgba, (pos_x, pos_y), prod_rgba)
    return comp


def generate_2d_studio_product(
    sku: str,
    source_img_path: Path | str,
    target_ground_y: int = 980,
    target_height: int = 720,
    auto_approve: bool = True
) -> Path:
    """
    Quy trình cốt lõi tạo 1 ảnh sản phẩm chuẩn Benchmark BIS Textile (1254x1254):
    - Tự động nạp BIS_BACKDROP_1254.png (hoặc BIS_BACKGROUND.png scale 1254x1254)
    - Tách nền quang học, khử răng cưa viền (Antialiasing)
    - Làm nét không biến dạng (Zero-Hallucination): giữ nguyên 100% hình khối, chữ và logo
    - Cân chỉnh kích thước tỷ lệ vàng (~58% khung hình), chân đế chạm y = target_ground_y
    - Đổ bóng vật lý 3 lớp (AO + Soft Shadow + Subtle floor reflection)
    - Lưu thẳng vào thư mục Google Drive: 6_Final_Composites/{sku}.png và {sku}_final.jpg
    """
    clean_sku = sku.strip().replace(" ", "_")
    src_p = Path(source_img_path)
    if not src_p.exists():
        raise FileNotFoundError(f"Không tìm thấy ảnh nguồn cho SKU {clean_sku} tại: {src_p}")

    # 1. Tải phôi nền BIS Textile chuẩn 1254x1254
    bg_p = find_bis_backdrop()
    backdrop = Image.open(bg_p).convert("RGBA").resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)

    # 2. Xử lý ảnh sản phẩm 2D
    raw_prod = Image.open(src_p)
    prod_clean = clean_and_cutout_product(raw_prod)

    # 3. Co giãn kích thước chuẩn catalogue (tỷ lệ 55% - 65% khung hình)
    orig_w, orig_h = prod_clean.size
    aspect = orig_w / orig_h
    h = target_height
    w = int(h * aspect)
    # Giới hạn chiều rộng không quá 880px để giữ cân đối trên khung hình 1254px
    if w > 880:
        w = 880
        h = int(w / aspect)

    prod_resized = prod_clean.resize((w, h), Image.Resampling.LANCZOS)
    prod_enhanced = enhance_product_sharpness(prod_resized, boost=1.6)

    # 4. Tính toán tọa độ đặt sản phẩm
    pos_x = (CANVAS_W - w) // 2
    pos_y = target_ground_y - h

    # 5. Đổ bóng vật lý 3 lớp
    composed = apply_2d_contact_shadow(
        backdrop=backdrop,
        prod_rgba=prod_enhanced,
        pos_x=pos_x,
        pos_y=pos_y,
        shadow_density=0.85,
        enable_reflection=True
    )

    # 6. Tinh chỉnh màu và hoàn thiện
    final_rgb = composed.convert("RGB")
    final_rgb = ImageEnhance.Sharpness(final_rgb).enhance(1.08)

    # 7. Lưu trực tiếp vào Google Drive theo chuẩn Benchmark PNG + JPG
    final_path_png = FINAL_DIR / f"{clean_sku}.png"
    final_path_jpg = FINAL_DIR / f"{clean_sku}_final.jpg"
    preview_path = PREVIEW_DIR / f"{clean_sku}_preview.jpg"

    final_rgb.save(final_path_png, format="PNG")
    final_rgb.save(final_path_jpg, format="JPEG", quality=96)
    final_rgb.save(preview_path, format="JPEG", quality=96)

    # 8. Cập nhật Manifest
    update_manifest(clean_sku, final_path_png, preview_path, approved=auto_approve)

    print(f"✓ ĐÃ HOÀN TẤT ẢNH CHUẨN BENCHMARK BIS 1254x1254 CHO SKU {clean_sku}: {final_path_png.resolve()}")
    return final_path_png


def update_manifest(sku: str, final_p: Path, preview_p: Path, approved: bool = True):
    """Cập nhật trạng thái vào image_review_manifest.json"""
    manifest = {}
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            manifest = {}

    status_str = "APPROVED" if approved else "PENDING_REVIEW"
    manifest[sku] = {
        "sku": sku,
        "status": status_str,
        "render_mode": "2D Studio BIS Textile (Chuẩn Mẫu)",
        "source": "FLOW_2D_STUDIO",
        "final_image": str(final_p),
        "preview_image": str(preview_p),
        "approved_at": time.strftime("%Y-%m-%d %H:%M:%S") if approved else None,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def find_source_image_for_sku(sku: str) -> Optional[Path]:
    """Tìm ảnh nguồn của SKU trong thư mục 4_Product_Images"""
    clean_sku = sku.strip().replace(" ", "_")
    clean_sku_lower = clean_sku.lower()

    # 1. Khớp chính xác tên file
    for ext in [".jpg", ".png", ".jpeg", ".webp"]:
        p = PRODUCT_DIR / f"{clean_sku}{ext}"
        if p.exists():
            return p

    # 2. Khớp tiền tố (ví dụ 03026A_brand_1.jpg, 03004A.jpg)
    for f in sorted(PRODUCT_DIR.iterdir()):
        if f.is_file() and (f.stem.lower() == clean_sku_lower or f.stem.lower().startswith(f"{clean_sku_lower}_")):
            if f.suffix.lower() in [".jpg", ".png", ".jpeg", ".webp"] and "BIS_BACKGROUND" not in f.name:
                return f

    return None


def run_batch_flow(skip_existing: bool = False) -> Dict[str, str]:
    """
    Chạy tự động hóa hàng loạt cho toàn bộ danh mục sản phẩm:
    - Quét file extracted_products_cache.json
    - Tìm ảnh nguồn tương ứng
    - Tạo ảnh 2D chuẩn và lưu thẳng vào Google Drive
    """
    cache_file = PROJECT_DIR / "extracted_products_cache.json"
    if not cache_file.exists():
        print("❌ Không tìm thấy file extracted_products_cache.json")
        return {}

    with open(cache_file, "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"🚀 BẮT ĐẦU CHẠY BATCH 2D FLOW CHO {len(products)} SẢN PHẨM...")
    results = {}
    success_cnt = 0
    skipped_cnt = 0
    missing_cnt = 0

    for idx, p in enumerate(products, 1):
        sku = p.get("sku", "").strip()
        if not sku:
            continue

        clean_sku = sku.replace(" ", "_")
        final_file = FINAL_DIR / f"{clean_sku}_final.jpg"

        if skip_existing and final_file.exists():
            print(f"[{idx}/{len(products)}] SKU {clean_sku}: Đã có ảnh hoàn thiện (Bỏ qua).")
            skipped_cnt += 1
            results[clean_sku] = "SKIPPED_EXISTS"
            continue

        src_img = find_source_image_for_sku(clean_sku)
        if not src_img:
            # Thử trích xuất từ PDF nếu có page_num
            page_num = p.get("source_page", 1)
            pdf_path = STORAGE_DIR / "1_Catalogues" / "catalogue_sample.pdf"
            if not pdf_path.exists():
                pdf_path = PROJECT_DIR / "catalogue_sample.pdf"
            
            if pdf_path.exists():
                try:
                    import pymupdf
                    doc = pymupdf.open(str(pdf_path))
                    if 1 <= page_num <= len(doc):
                        page = doc[page_num - 1]
                        imgs = page.get_images()
                        if imgs:
                            base_img = doc.extract_image(imgs[0][0])
                            extracted_path = PRODUCT_DIR / f"{clean_sku}.jpg"
                            with open(extracted_path, "wb") as ef:
                                ef.write(base_img["image"])
                            src_img = extracted_path
                    doc.close()
                except Exception:
                    pass

        if not src_img:
            print(f"[{idx}/{len(products)}] ⚠️ SKU {clean_sku}: Chưa có ảnh nguồn trong Drive.")
            missing_cnt += 1
            results[clean_sku] = "MISSING_SOURCE"
            continue

        try:
            out_p = generate_2d_studio_product(clean_sku, src_img, auto_approve=True)
            print(f"[{idx}/{len(products)}] ✅ SKU {clean_sku}: Thành công -> {out_p.name}")
            success_cnt += 1
            results[clean_sku] = "SUCCESS"
        except Exception as e:
            print(f"[{idx}/{len(products)}] ❌ SKU {clean_sku}: Lỗi - {e}")
            results[clean_sku] = f"ERROR: {e}"

    print(f"\n🎉 TỔNG KẾT BATCH FLOW:")
    print(f"- Thành công: {success_cnt} ảnh")
    print(f"- Bỏ qua (đã có): {skipped_cnt} ảnh")
    print(f"- Chưa có ảnh nguồn: {missing_cnt} ảnh")
    print(f"📁 Thư mục lưu trữ: {FINAL_DIR.resolve()}\n")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BIS Textile - 2D Studio Background Flow")
    parser.add_argument("--sku", type=str, help="Tạo ảnh cho 1 mã SKU cụ thể (vd: 03004A)")
    parser.add_argument("--all", action="store_true", help="Chạy tự động cho toàn bộ danh mục sản phẩm")
    parser.add_argument("--skip-existing", action="store_true", help="Bỏ qua các SKU đã có ảnh thành phẩm")

    args = parser.parse_args()

    if args.sku:
        src = find_source_image_for_sku(args.sku)
        if not src:
            print(f"❌ Không tìm thấy ảnh nguồn cho SKU {args.sku} trong {PRODUCT_DIR}")
            sys.exit(1)
        generate_2d_studio_product(args.sku, src, auto_approve=True)
    elif args.all:
        run_batch_flow(skip_existing=args.skip_existing)
    else:
        # Mặc định: Thử chạy mẫu trên SKU 03004A và 03026A
        print("💡 Đang chạy kiểm thử 2D Flow cho các SKU có sẵn...")
        for sample_sku in ["03004A", "03026A"]:
            src = find_source_image_for_sku(sample_sku)
            if src:
                generate_2d_studio_product(sample_sku, src, auto_approve=True)

