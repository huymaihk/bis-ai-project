"""
BIS Textile AI - Agent Media (Creative Studio & Product Image Compositing)
Responsible for:
- Fetching official brand images (max 2) named by SKU: {sku}_brand_1.jpg, {sku}_brand_2.jpg
- Storing user-supplied real product photos named by SKU: {sku}_user_1.jpg
- AI image compositing: Merging product cutout onto user-selected background mockup
- Realistic rendering (soft drop shadow, lighting balance, photorealistic feel)
- Human Review Gate: Holds images in PENDING_REVIEW until explicitly APPROVED by user
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw

class AgentMedia:
    def __init__(self, workspace_dir: str | Path | None = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path(__file__).parent.resolve()
        self.media_vault = self.workspace_dir / "media_vault"
        
        self.brand_dir = self.media_vault / "raw_brand"
        self.user_dir = self.media_vault / "user_uploads"
        self.bg_dir = self.media_vault / "backgrounds"
        self.final_dir = self.media_vault / "final_composites"
        
        for d in [self.brand_dir, self.user_dir, self.bg_dir, self.final_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.manifest_path = self.media_vault / "image_review_manifest.json"
        self.manifest = self._load_manifest()
        self._ensure_sample_backgrounds()

    def _load_manifest(self) -> Dict[str, dict]:
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_manifest(self):
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)

    def _ensure_sample_backgrounds(self):
        """Create sample studio & lab background mockups if empty."""
        lab_bg = self.bg_dir / "modern_textile_lab.jpg"
        studio_bg = self.bg_dir / "clean_studio_gradient.jpg"
        
        if not lab_bg.exists():
            # Tạo nền gradient phòng lab tối giản
            img = Image.new("RGB", (1000, 1000), "#f1f5f9")
            draw = ImageDraw.Draw(img)
            # Tạo hiệu ứng mặt bàn thí nghiệm phẳng
            draw.rectangle([0, 700, 1000, 1000], fill="#e2e8f0")
            draw.line([(0, 700), (1000, 700)], fill="#cbd5e1", width=2)
            img.save(lab_bg, quality=95)

        if not studio_bg.exists():
            # Tạo nền studio xám nhạt cao cấp
            img = Image.new("RGB", (1000, 1000), "#ffffff")
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, 750, 1000, 1000], fill="#f8fafc")
            draw.line([(0, 750), (1000, 750)], fill="#e2e8f0", width=1)
            img.save(studio_bg, quality=95)

    def register_user_image(self, sku: str, image_bytes: bytes, filename: str) -> Path:
        """Save user supplied product photo with strict SKU naming format."""
        clean_sku = sku.strip().replace(" ", "_")
        target_path = self.user_dir / f"{clean_sku}_user_1.jpg"
        with open(target_path, "wb") as f:
            f.write(image_bytes)
        return target_path

    def register_background(self, name: str, image_bytes: bytes) -> Path:
        """Save a new user-supplied background template."""
        clean_name = name.strip().replace(" ", "_").lower()
        if not clean_name.endswith(".jpg") and not clean_name.endswith(".png"):
            clean_name += ".jpg"
        target_path = self.bg_dir / clean_name
        with open(target_path, "wb") as f:
            f.write(image_bytes)
        return target_path

    def get_backgrounds(self) -> List[Path]:
        """Return list of available background templates."""
        return list(self.bg_dir.glob("*.jpg")) + list(self.bg_dir.glob("*.png"))

    def composite_product_image(self, sku: str, product_img_path: Path, bg_path: Path) -> Path:
        """
        Merge product cutout onto chosen background mockup with realistic drop shadow.
        Output: {sku}_final.jpg
        """
        clean_sku = sku.strip().replace(" ", "_")
        final_path = self.final_dir / f"{clean_sku}_final.jpg"

        bg_img = Image.open(bg_path).convert("RGBA").resize((1000, 1000), Image.Resampling.LANCZOS)
        prod_img = Image.open(product_img_path).convert("RGBA")

        # Tự động loại bỏ nền trắng đơn sắc nếu ảnh chưa có alpha kênh trong suốt
        datas = prod_img.getdata()
        new_data = []
        for item in datas:
            # Ngưỡng màu trắng gần tuyệt đối (RGB > 240)
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        prod_img.putdata(new_data)

        # Scale sản phẩm vừa vặn 65% khung hình
        max_size = 650
        prod_img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Tạo bóng đổ chân thực (Drop shadow) dưới chân sản phẩm
        shadow = Image.new("RGBA", (1000, 1000), (0, 0, 0, 0))
        prod_w, prod_h = prod_img.size
        pos_x = (1000 - prod_w) // 2
        pos_y = 680 - prod_h  # Đặt sản phẩm đứng trên mặt bàn

        # Vẽ bóng elip mềm
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_box = [pos_x + 20, 675, pos_x + prod_w - 20, 715]
        shadow_draw.ellipse(shadow_box, fill=(30, 41, 59, 130))
        shadow = shadow.filter(ImageFilter.GaussianBlur(14))

        # Ghép: Nền -> Bóng đổ -> Sản phẩm
        composed = Image.alpha_composite(bg_img, shadow)
        composed.paste(prod_img, (pos_x, pos_y), prod_img)

        # Tinh chỉnh màu sắc & độ sắc nét (Photorealistic enhance)
        enhancer = ImageEnhance.Sharpness(composed.convert("RGB"))
        final_img = enhancer.enhance(1.15)
        color_enhancer = ImageEnhance.Color(final_img)
        final_img = color_enhancer.enhance(1.05)

        final_img.save(final_path, quality=95)

        # Ghi nhận trạng thái PENDING_REVIEW
        self.manifest[clean_sku] = {
            "sku": clean_sku,
            "status": "PENDING_REVIEW",
            "final_image": str(final_path),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save_manifest()
        return final_path

    def approve_image(self, sku: str) -> bool:
        """Mark image as APPROVED for Haravan sync."""
        clean_sku = sku.strip().replace(" ", "_")
        if clean_sku in self.manifest:
            self.manifest[clean_sku]["status"] = "APPROVED"
            self.manifest[clean_sku]["approved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self._save_manifest()
            return True
        return False

    def reject_image(self, sku: str, reason: str = "") -> bool:
        """Reject and request re-compositing."""
        clean_sku = sku.strip().replace(" ", "_")
        if clean_sku in self.manifest:
            self.manifest[clean_sku]["status"] = "REJECTED"
            self.manifest[clean_sku]["reject_reason"] = reason
            self._save_manifest()
            return True
        return False

