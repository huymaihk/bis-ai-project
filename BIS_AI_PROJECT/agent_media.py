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
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw

class AgentMedia:
    def __init__(self, workspace_dir: str | Path | None = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path(__file__).parent.resolve()
        self.gdrive_storage = self.workspace_dir / "Google_Drive_Storage"
        self.gdrive_storage.mkdir(parents=True, exist_ok=True)
        
        # Thư mục hình ảnh lưu trữ trực tiếp trên Google Drive
        self.brand_dir = self.gdrive_storage / "4_Product_Images"
        self.user_dir = self.gdrive_storage / "4_Product_Images"
        self.bg_dir = self.gdrive_storage / "5_Studio_Backgrounds"
        self.final_dir = self.gdrive_storage / "6_Final_Composites"
        
        self.preview_dir = self.gdrive_storage / "5_Draft_Previews"
        for d in [self.brand_dir, self.user_dir, self.bg_dir, self.preview_dir, self.final_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.manifest_path = self.gdrive_storage / "image_review_manifest.json"
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
        """Khởi tạo bộ thư viện 3 phông nền Studio 3D chân thực cao cấp nếu chưa có."""
        p_podium = self.bg_dir / "luxury_marble_podium.jpg"
        p_lab = self.bg_dir / "modern_textile_lab.jpg"
        p_studio = self.bg_dir / "clean_studio_gradient.jpg"

        # 1. Bục đá Marble & Đèn Sân Khấu (luxury_marble_podium.jpg)
        if not p_podium.exists():
            img1 = Image.new("RGB", (1000, 1000), "#0b1120")
            d1 = ImageDraw.Draw(img1)
            for r in range(500, 0, -15):
                alpha = int(100 * (1 - r / 500))
                d1.ellipse([500 - r, 320 - int(r*0.6), 500 + r, 320 + int(r*0.6)], fill=(20 + alpha//2, 30 + alpha//2, 45 + alpha))
            for y in range(650, 1000):
                ratio = (y - 650) / 350
                color = (int(15 + 20 * ratio), int(23 + 25 * ratio), int(42 + 30 * ratio))
                d1.line([(0, y), (1000, y)], fill=color)
            d1.rectangle([500 - 320, 720, 500 + 320, 720 + 45], fill=(203, 213, 225))
            d1.ellipse([500 - 320, 720 - 55, 500 + 320, 720 + 55], fill=(241, 245, 249))
            d1.ellipse([500 - 315, 720 - 52, 500 + 315, 720 + 52], outline=(255, 255, 255), width=2)
            d1.ellipse([500 - 320, 720 + 45 - 55, 500 + 320, 720 + 45 + 55], fill=(148, 163, 184))
            img1 = img1.filter(ImageFilter.GaussianBlur(1))
            img1.save(p_podium, quality=95)

        # 2. Bàn thí nghiệm Dệt may Công nghệ cao (modern_textile_lab.jpg)
        if not p_lab.exists() or p_lab.stat().st_size < 19000:
            img2 = Image.new("RGB", (1000, 1000), "#f8fafc")
            d2 = ImageDraw.Draw(img2)
            for y in range(0, 680):
                val = int(240 - 20 * (y / 680))
                d2.line([(0, y), (1000, y)], fill=(val - 10, val - 5, val))
            d2.line([(0, 680), (1000, 680)], fill="#94a3b8", width=2)
            for y in range(680, 1000):
                ratio = (y - 680) / 320
                c_val = int(220 + 25 * ratio)
                d2.line([(0, y), (1000, y)], fill=(c_val - 5, c_val, c_val + 5))
            d2.ellipse([150, 685, 850, 720], fill=(255, 255, 255, 120))
            img2 = img2.filter(ImageFilter.GaussianBlur(1))
            img2.save(p_lab, quality=95)

        # 3. Studio xám khói tối giản (clean_studio_gradient.jpg)
        if not p_studio.exists() or p_studio.stat().st_size < 19000:
            img3 = Image.new("RGB", (1000, 1000), "#ffffff")
            d3 = ImageDraw.Draw(img3)
            for y in range(0, 1000):
                val = int(255 - 45 * (y / 1000))
                d3.line([(0, y), (1000, y)], fill=(val, val, val + 2))
            d3.ellipse([150, 700, 850, 780], fill="#f1f5f9", outline="#e2e8f0", width=1)
            img3 = img3.filter(ImageFilter.GaussianBlur(1))
            img3.save(p_studio, quality=95)

    def extract_images_from_exact_page(self, pdf_path: str | Path, page_num: int, min_width: int = 60, min_height: int = 60) -> list[dict]:
        """
        Bóc tách toàn bộ hình ảnh nằm chính xác trên trang page_num của Catalogue PDF.
        Không nhảy sang trang khác để tránh trích nhầm sản phẩm.
        Trả về danh sách dict: xref, width, height, size_bytes, ext, image_bytes, page_num.
        """
        import pymupdf
        if not os.path.exists(str(pdf_path)):
            possible_paths = [
                self.workspace_dir / "catalogue_sample.pdf",
                self.gdrive_storage / "1_Catalogues" / "catalogue_sample.pdf",
                self.workspace_dir.parent / "catalogue_sample.pdf",
            ]
            for p in possible_paths:
                if p.exists():
                    pdf_path = p
                    break
            else:
                return []

        results = []
        try:
            doc = pymupdf.open(str(pdf_path))
            total_pages = len(doc)
            if not (1 <= page_num <= total_pages):
                doc.close()
                return []

            page = doc[page_num - 1]
            img_list = page.get_images(full=True)
            seen_xrefs = set()

            for img_info in img_list:
                xref = img_info[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                try:
                    base_img = doc.extract_image(xref)
                    img_bytes = base_img["image"]
                    w, h = base_img["width"], base_img["height"]
                    ext = base_img["ext"]
                    if w >= min_width and h >= min_height and len(img_bytes) >= 1500:
                        results.append({
                            "xref": xref,
                            "width": w,
                            "height": h,
                            "size_bytes": len(img_bytes),
                            "ext": ext,
                            "image_bytes": img_bytes,
                            "page_num": page_num
                        })
                except Exception:
                    continue

            doc.close()
            # Sắp xếp ảnh có kích thước byte lớn nhất lên đầu
            results.sort(key=lambda x: x["size_bytes"], reverse=True)
        except Exception as e:
            print(f"Error extracting images from exact page {page_num}: {e}")
        return results

    def save_image_bytes_as_brand(self, sku: str, image_bytes: bytes, index: int = 1) -> Path:
        """Lưu trực tiếp mảng bytes ảnh vào thư mục ảnh chính hãng trên Google Drive."""
        clean_sku = sku.strip().replace(" ", "_")
        target_path = self.brand_dir / f"{clean_sku}_brand_{index}.jpg"
        with open(target_path, "wb") as f:
            f.write(image_bytes)
        print(f"✓ Đã lưu ảnh {clean_sku}_brand_{index}.jpg ({len(image_bytes):,} bytes)")
        return target_path

    def extract_image_from_pdf(self, sku: str, pdf_path: str | Path, page_num: int, product_name: str = "", scan_all: bool = False) -> Optional[Path]:
        """
        Bóc ảnh thiết bị từ Catalogue PDF:
        - Kiểm tra nếu tên sản phẩm thuộc dạng sách/tiêu chuẩn (manual, standard, tiêu chuẩn, book, aatcc, iso):
          Ưu tiên tìm ảnh Web (ảnh bìa sách) thay vì bóc tách ảnh thiết bị từ PDF.
        - BƯỚC 1: Quét chính xác trang `page_num` (source_page). Nếu trang có ảnh > 5KB, lấy ảnh nét nhất trên ĐÚNG TRANG ĐÓ.
        - BƯỚC 2: Chỉ khi trang đó không có ảnh và scan_all=True (và không phải dạng sách/tiêu chuẩn) thì mới quét các trang khác chứa đúng mã SKU.
        - XÓA BỎ HOÀN TOÀN đoạn fallback pixmap chụp nguyên trang bìa. Nếu không có ảnh > 5KB, trả về None để kích hoạt tìm kiếm Web.
        """
        # Candidate selection must happen in the UI; a page can contain multiple SKUs.
        from pdf_candidates import candidates
        self.last_pdf_candidates = candidates(pdf_path, sku)
        return None

    def clean_search_query(self, query: str) -> str:
        """Lọc bỏ các từ khóa bị lặp lại, giữ nguyên thứ tự các từ có nghĩa."""
        if not query:
            return ""
        words = []
        seen = set()
        for w in query.split():
            lw = w.lower()
            if lw not in seen:
                seen.add(lw)
                words.append(w)
        return " ".join(words)

    def search_google_custom_search(self, query: str, max_results: int = 8) -> list[dict]:
        """
        Tìm kiếm ảnh trực tiếp qua Google Programmable Search Engine JSON API.
        Kích hoạt nếu có cấu hình GOOGLE_SEARCH_API_KEY và GOOGLE_SEARCH_CX.
        """
        import os
        import requests
        api_key = os.environ.get("GOOGLE_SEARCH_API_KEY")
        cx = os.environ.get("GOOGLE_SEARCH_CX")

        if not (api_key and cx):
            try:
                import streamlit as st
                api_key = api_key or st.secrets.get("GOOGLE_SEARCH_API_KEY")
                cx = cx or st.secrets.get("GOOGLE_SEARCH_CX")
            except Exception:
                pass

        if not (api_key and cx):
            return []

        try:
            clean_q = self.clean_search_query(query)
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "q": clean_q,
                "cx": cx,
                "key": api_key,
                "searchType": "image",
                "num": min(max_results, 10)
            }
            res = requests.get(url, params=params, timeout=12)
            if res.status_code == 200:
                data = res.json()
                results = []
                for item in data.get("items", []):
                    img_info = item.get("image", {})
                    results.append({
                        "image_url": item.get("link"),
                        "thumb_url": img_info.get("thumbnailLink") or item.get("link"),
                        "title": item.get("title", clean_q),
                        "page_url": img_info.get("contextLink", ""),
                        "domain": item.get("displayLink", "Google")
                    })
                if results:
                    print(f"✓ Đã lấy {len(results)} ảnh sạch từ Google Custom Search JSON API")
                    return results
        except Exception as e:
            print(f"Lỗi tìm kiếm ảnh qua Google Custom Search API: {e}")
        return []

    def preprocess_search_query(self, query: str) -> str:
        """
        Rút gọn và tiền xử lý từ khóa tìm ảnh:
        - Lọc bỏ các hư từ (of, and, the, procedures, methods, hardbound, book, standard, test, -, :).
        - Chỉ giữ lại: [Brand] + [SKU] + [2-3 từ định danh cốt lõi].
        """
        return self.clean_search_query(query or "")

    def search_web_images(self, query: str, max_results: int = 8) -> list[dict]:
        """
        Tìm kiếm ảnh sản phẩm qua DuckDuckGo (DDGS):
        - Dùng DDGS().images() thay thế hoàn toàn cho Bing HTML scraping.
        - Tiền xử lý rút gọn từ khóa: tự động lọc bỏ các hư từ, giữ lại Brand + SKU + 2-3 từ định danh cốt lõi.
        - Bổ sung bộ lọc danh sách đen: loại bỏ ngay kết quả có domain/title chứa: meme, cat, kitty, boredpanda, bing, wallpaper, avatar, ads...
        """
        short_query = self.preprocess_search_query(query)
        if not short_query:
            return []

        # Danh sách đen loại trừ: meme, mèo, mạng xã hội, quảng cáo
        blacklist = [
            "meme", "cat", "kitty", "kitten", "dog", "puppy", "funny", "boredpanda",
            "wallpaper", "avatar", "ads", "bing", "reddit", "facebook", "pinterest",
            "cashback", "coupon", "discount", "gift card", "tiktok", "instagram"
        ]

        results = []
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                try:
                    ddgs_gen = ddgs.images(
                        query=short_query,
                        region="wt-wt",
                        safesearch="off",
                        max_results=max_results * 2
                    )
                except TypeError:
                    ddgs_gen = ddgs.images(
                        keywords=short_query,
                        region="wt-wt",
                        safesearch="off",
                        max_results=max_results * 2
                    )

                for r in ddgs_gen:
                    title = (r.get("title") or "").lower()
                    img_url = (r.get("image") or "").lower()
                    domain = (r.get("source") or "").lower()

                    # Bỏ qua nếu dính danh sách đen
                    if any(__import__("re").search(r"\\b"+__import__("re").escape(bad)+r"\\b", title+" "+domain) for bad in blacklist):
                        continue

                    raw_img = r.get("image")
                    if raw_img:
                        results.append({
                            "image_url": raw_img,
                            "thumb_url": r.get("thumbnail") or raw_img,
                            "title": r.get("title", short_query),
                            "page_url": r.get("url") or "",
                            "domain": r.get("source") or "DuckDuckGo"
                        })
                    if len(results) >= max_results:
                        break

            if results:
                print(f"✓ Đã tìm thấy {len(results)} ảnh sạch qua DuckDuckGo cho '{short_query}'")
                return results
        except Exception as e:
            print(f"Lỗi tìm kiếm ảnh DDGS cho '{short_query}': {e}")

        # Fallback 1: Google Custom Search API nếu có cấu hình API Key & CX
        google_res = self.search_google_custom_search(short_query, max_results=max_results)
        if google_res:
            return google_res

        return results

    def search_duckduckgo_images(self, query: str, max_results: int = 8) -> list[dict]:
        """Tương thích ngược: gọi trực tiếp search_web_images."""
        return self.search_web_images(query, max_results=max_results)

    def download_and_save_brand_image(self, sku: str, image_url: str, index: int = 1) -> Optional[Path]:
        """Tải ảnh từ URL đã chọn và lưu vào thư mục ảnh hãng của SKU trên Google Drive."""
        from media_quality import download_image, safe_name, checked_image
        try:
            data = download_image(image_url)
            image = checked_image(data)
            target = self.brand_dir / f"{safe_name(sku)}_brand_{index}.png"
            image.save(target, format="PNG")
            return target
        except Exception:
            return None

    def fetch_brand_image_from_web(self, sku: str, brand_name: str, title: str, product_name_vi: str = "") -> Optional[Path]:
        """
        Tìm và lưu ảnh sản phẩm thực tế từ Web kết hợp thông minh:
        - Tên hãng (Brand) + Mã SKU + Tên sản phẩm tiếng Anh / tiếng Việt.
        """
        from media_quality import rank_candidates
        query = f'{brand_name} "{sku}" {title}'
        self.last_web_candidates = rank_candidates(self.search_web_images(query), sku, title, brand_name)
        # Human selection is required; no "first downloaded image = verified" fallback.
        return None

    def get_product_image_for_sku(self, sku: str) -> Optional[Path]:
        """
        Tìm kiếm ảnh sản phẩm do người dùng đặt vào Google Drive khớp với mã SKU:
        Tìm trong thư mục Google_Drive_Storage/4_Product_Images/ với các mẫu:
        - {sku}.jpg, {sku}.png, {sku}.jpeg, {sku}.webp
        - {sku}_brand_1.jpg, {sku}_user_1.jpg, {sku}_1.jpg, {sku}_*.*
        - Không phân biệt hoa thường và tự động chuẩn hóa dấu cách thành gạch dưới.
        """
        clean_sku = sku.strip().replace(" ", "_")
        clean_sku_lower = clean_sku.lower()
        chosen = self.user_dir / f"{sku}_user_1.png"
        if chosen.exists():
            return chosen
        search_dirs = [self.user_dir, self.brand_dir]

        # 1. Khớp chính xác {sku}.ext
        for d in search_dirs:
            if not d.exists():
                continue
            for ext in [".jpg", ".png", ".jpeg", ".webp"]:
                p = d / f"{clean_sku}{ext}"
                if p.exists():
                    return p
            for f in d.iterdir():
                if f.is_file() and f.stem.lower() == clean_sku_lower and f.suffix.lower() in [".jpg", ".png", ".jpeg", ".webp"]:
                    return f

        # 2. Khớp các tiền tố {sku}_* (ví dụ 03026A_brand_1.jpg, 03026A_user_1.jpg)
        for d in search_dirs:
            if not d.exists():
                continue
            for f in sorted(d.iterdir()):
                if f.is_file() and f.stem.lower().startswith(f"{clean_sku_lower}_") and f.suffix.lower() in [".jpg", ".png", ".jpeg", ".webp"]:
                    return f

        return None

    def register_user_image(self, sku: str, image_bytes: bytes, filename: str) -> Path:
        """Save user supplied product photo with strict SKU naming format."""
        from media_quality import checked_image, safe_name
        image = checked_image(image_bytes)
        target_path = self.user_dir / f"{safe_name(sku)}_user_1.png"
        image.save(target_path, format="PNG")
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
        """Return list of available background templates, prioritizing 1254x1254 BIS backdrop."""
        bgs = list(self.bg_dir.glob("*.jpg")) + list(self.bg_dir.glob("*.png"))
        def sort_priority(p: Path):
            name = p.name.lower()
            if "bis_backdrop_1254" in name:
                return 0
            if "bis_background" in name:
                return 1
            return 2
        return sorted(bgs, key=sort_priority)

    def create_3d_branded_backdrop(
        self, 
        pattern_img_path: Path | str, 
        canvas_w: int = 1000, 
        canvas_h: int = 1000, 
        horizon_y: int = 550, 
        depth_ratio: float = 0.20
    ) -> Image.Image:
        """
        Dựng phông nền 3D Tường - Sàn không gian thương hiệu từ phôi hoa văn lặp logo (OpenCV Perspective Warp):
        - Phần tường đứng (y: 0 -> horizon_y): Giữ nguyên tỷ lệ 2D phẳng.
        - Phần mặt sàn (y: horizon_y -> canvas_h): Dùng cv2.getPerspectiveTransform và cv2.warpPerspective
          với cạnh trên thu hẹp depth_ratio (15%-35%) và cạnh đáy mở rộng 0%-100% tạo cảm giác sàn trải dài có chiều sâu.
        - Tạo đường viền giao thoa giữa chân tường và mặt sàn với dải gradient bóng đổ mềm.
        """
        import cv2
        import numpy as np
        
        p = Path(pattern_img_path)
        if not p.exists():
            for pos in [
                self.bg_dir / "BIS_BACKGROUND.png",
                self.user_dir / "BIS_BACKGROUND.png",
                self.workspace_dir / "Google_Drive_Storage" / "4_Product_Images" / "BIS_BACKGROUND.png"
            ]:
                if pos.exists():
                    p = pos
                    break
        
        pat = Image.open(p).convert("RGB") if p.exists() else Image.new("RGB", (canvas_w, canvas_h), "#ffffff")
        
        wall_h = max(20, min(canvas_h - 20, horizon_y))
        floor_h = canvas_h - wall_h
        
        # 1. Phần tường đứng (Wall 2D phẳng)
        wall_img = pat.resize((canvas_w, wall_h), Image.Resampling.LANCZOS)
        
        # 2. Phần mặt sàn (Floor 3D Perspective Warp)
        floor_raw = pat.resize((canvas_w, floor_h), Image.Resampling.LANCZOS)
        floor_np = np.array(floor_raw)
        
        src_pts = np.float32([
            [0, 0],
            [canvas_w, 0],
            [canvas_w, floor_h],
            [0, floor_h]
        ])
        
        shrink_px = int(canvas_w * float(depth_ratio))
        dst_pts = np.float32([
            [shrink_px, 0],
            [canvas_w - shrink_px, 0],
            [canvas_w, floor_h],
            [0, floor_h]
        ])
        
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warped_floor_np = cv2.warpPerspective(
            floor_np, M, (canvas_w, floor_h), 
            borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255)
        )
        warped_floor = Image.fromarray(warped_floor_np)
        
        # 3. Ghép Tường và Sàn
        backdrop = Image.new("RGB", (canvas_w, canvas_h))
        backdrop.paste(wall_img, (0, 0))
        backdrop.paste(warped_floor, (0, wall_h))
        
        # 4. Tạo đường viền giao thoa chân tường - mặt sàn (Crease gradient shadow)
        crease = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        c_draw = ImageDraw.Draw(crease)
        for i in range(16):
            alpha = int(90 * (1.0 - i / 16.0))
            c_draw.line([(0, wall_h + i), (canvas_w, wall_h + i)], fill=(0, 0, 0, alpha))
        for i in range(8):
            alpha = int(55 * (1.0 - i / 8.0))
            c_draw.line([(0, wall_h - i), (canvas_w, wall_h - i)], fill=(0, 0, 0, alpha))
            
        backdrop_rgba = backdrop.convert("RGBA")
        return Image.alpha_composite(backdrop_rgba, crease)

    def apply_realistic_contact_shadow(
        self,
        backdrop: Image.Image,
        prod_rgba: Image.Image,
        pos_x: int,
        pos_y: int,
        shadow_density: float = 0.80,
        enable_reflection: bool = True,
        sharpness_boost: float = 1.8
    ) -> Image.Image:
        """
        Hệ thống đổ bóng vật lý đa tầng và phản xạ mờ mặt sàn (Physics-based Contact Shadow):
        - Lớp 1 (Ambient Occlusion): Bóng tiếp xúc đáy chân đế cực đậm và dẹp (opacity ~75-80%).
        - Lớp 2 (Soft Drop Shadow): Bóng tỏa mềm làm mờ Gaussian (radius=12-16, opacity ~35%).
        - Phản xạ mờ (Subtle Mirror/Reflection): Lật 18-22% đáy sản phẩm với mặt nạ gradient 10-15% tạo hiệu ứng sàn mica/gạch bóng.
        """
        import numpy as np
        canvas_w, canvas_h = backdrop.size
        prod_w, prod_h = prod_rgba.size
        ground_y = pos_y + prod_h
        
        comp = backdrop.copy().convert("RGBA")
        
        # 1. Subtle Mirror Reflection (Phản xạ mờ mặt sàn)
        if enable_reflection:
            refl_h = max(int(prod_h * 0.20), 10)
            bottom_part = prod_rgba.crop((0, prod_h - refl_h, prod_w, prod_h))
            flipped = bottom_part.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            
            grad_mask = Image.new("L", (prod_w, refl_h), 0)
            g_draw = ImageDraw.Draw(grad_mask)
            for y in range(refl_h):
                val = int(38 * (1.0 - y / refl_h))
                g_draw.line([(0, y), (prod_w, y)], fill=val)
                
            f_r, f_g, f_b, f_a = flipped.split()
            comb_a = Image.fromarray((np.array(f_a).astype(float) * np.array(grad_mask).astype(float) / 255.0).astype(np.uint8))
            flipped.putalpha(comb_a)
            flipped = flipped.filter(ImageFilter.GaussianBlur(1.5))
            
            refl_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            refl_layer.paste(flipped, (pos_x, ground_y))
            comp = Image.alpha_composite(comp, refl_layer)
        
        # 2. Lớp 2 - Soft Drop Shadow (Bóng tỏa mềm)
        soft_shadow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(soft_shadow)
        soft_opacity = int(75 * float(shadow_density))
        soft_w_expand = int(prod_w * 0.14)
        soft_h = max(int(prod_h * 0.08), 22)
        soft_box = [
            pos_x - soft_w_expand,
            ground_y - int(soft_h * 0.25),
            pos_x + prod_w + soft_w_expand,
            ground_y + int(soft_h * 1.15)
        ]
        s_draw.ellipse(soft_box, fill=(15, 20, 30, soft_opacity))
        soft_shadow = soft_shadow.filter(ImageFilter.GaussianBlur(14))
        comp = Image.alpha_composite(comp, soft_shadow)
        
        # 3. Lớp 1 - Ambient Occlusion (Bóng tiếp xúc chân đế cực đậm và dẹp)
        ao_shadow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        ao_draw = ImageDraw.Draw(ao_shadow)
        ao_opacity = int(215 * float(shadow_density))
        ao_h = max(int(prod_h * 0.026), 7)
        ao_box = [
            pos_x + int(prod_w * 0.04),
            ground_y - int(ao_h * 0.6),
            pos_x + prod_w - int(prod_w * 0.04),
            ground_y + int(ao_h * 0.75)
        ]
        ao_draw.ellipse(ao_box, fill=(10, 15, 25, ao_opacity))
        ao_shadow = ao_shadow.filter(ImageFilter.GaussianBlur(3))
        comp = Image.alpha_composite(comp, ao_shadow)
        
        # 4. Ghép sản phẩm lên trên cùng
        comp.paste(prod_rgba, (pos_x, pos_y), prod_rgba)
        return comp

    def _find_perspective_coeffs(self, dst_pts, src_pts):
        """Tính toán ma trận hệ số biến đổi phối cảnh 3D (Pillow Perspective Transform)."""
        import numpy as np
        matrix = []
        for p1, p2 in zip(dst_pts, src_pts):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
        A = np.matrix(matrix, dtype=float)
        B = np.array(src_pts).reshape(8)
        res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
        return np.array(res).reshape(8)

    def render_3d_book_mockup(self, cover_img: Image.Image, target_height: int = 540) -> Image.Image:
        """
        Dựng hình Sách & Tài liệu 3D siêu thực:
        1. Uốn nghiêng bìa trước theo góc phối cảnh 3D (~12 độ)
        2. Sinh gáy sách cong (3D Curved Spine) với màu đồng bộ và dải sáng Highlight
        3. Sinh khối trang giấy (Page block edges) bên phải và đáy
        """
        import numpy as np
        orig_w, orig_h = cover_img.size
        aspect = orig_w / orig_h
        h = target_height
        w = max(int(h * aspect), 180)
        
        cover = cover_img.convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
        cover = ImageEnhance.Sharpness(cover).enhance(1.3)

        spine_w = max(int(w * 0.12), 22)
        canvas_w = w + spine_w + 60
        canvas_h = h + 80

        # Tọa độ 4 góc của bìa trước nghiêng 3D
        p_tl = (spine_w, int(h * 0.05))
        p_tr = (w + spine_w - 15, int(h * 0.02))
        p_br = (w + spine_w - 15, int(h * 0.94))
        p_bl = (spine_w, h)

        coeffs = self._find_perspective_coeffs([p_tl, p_tr, p_br, p_bl], [(0,0), (w,0), (w,h), (0,h)])
        warped_front = cover.transform((canvas_w, canvas_h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)

        # 2. Tạo gáy sách 3D cong (Spine)
        spine_img = Image.new("RGBA", (canvas_w, canvas_h), (0,0,0,0))
        s_draw = ImageDraw.Draw(spine_img)
        left_sample = cover.crop((0, 0, max(5, int(w*0.08)), h))
        stat = np.array(left_sample)
        avg_color = tuple(int(c * 0.75) for c in stat[:, :, :3].mean(axis=(0, 1)))

        p_s_tl = (12, int(h * 0.09))
        p_s_tr = p_tl
        p_s_br = p_bl
        p_s_bl = (12, int(h * 1.04))
        s_draw.polygon([p_s_tl, p_s_tr, p_s_br, p_s_bl], fill=(*avg_color, 255))

        # Dải sáng Highlight cong dọc gáy sách
        hl_color = tuple(min(255, int(c * 1.35)) for c in avg_color)
        s_draw.line([(p_s_tl[0] + 5, p_s_tl[1] + 2), (p_s_bl[0] + 5, p_s_bl[1] - 2)], fill=(*hl_color, 160), width=3)

        # 3. Tạo mép trang giấy (Page block) bên phải
        page_img = Image.new("RGBA", (canvas_w, canvas_h), (0,0,0,0))
        pg_draw = ImageDraw.Draw(page_img)
        p_pg_tr = (p_tr[0] + 16, p_tr[1] + 8)
        p_pg_br = (p_br[0] + 16, p_br[1] + 6)
        pg_draw.polygon([p_tr, p_pg_tr, p_pg_br, p_br], fill=(235, 230, 220, 255))
        for yy in range(p_tr[1] + 10, p_br[1], 4):
            pg_draw.line([(p_tr[0] + 2, yy), (p_pg_tr[0] - 2, yy + 2)], fill=(180, 175, 165, 180), width=1)

        # Ghép: Trang giấy -> Gáy sách -> Bìa trước
        book_composed = Image.alpha_composite(page_img, spine_img)
        book_composed = Image.alpha_composite(book_composed, warped_front)

        bbox = book_composed.getbbox()
        return book_composed.crop(bbox) if bbox else book_composed

    def smart_prepare_product(self, prod_img: Image.Image) -> Image.Image:
        """
        Tiền xử lý sản phẩm thông minh:
        - Tự động cắt bỏ viền đen (Black border padding) xung quanh ảnh scan bìa sách.
        - Dùng FloodFill từ các góc biên để loại bỏ nền trắng/xám bên ngoài mà KHÔNG làm thủng nền ruột bìa sách.
        - Giữ nguyên độ phân giải gốc của vật thể.
        """
        import cv2
        import numpy as np
        im = prod_img.convert("RGBA")
        arr = np.array(im)
        h, w = arr.shape[:2]
        
        # 1. Cắt bỏ viền đen nếu ảnh scan/ảnh web bị bọc khung đen
        if arr[:5, :, :3].mean() < 30 or arr[:, :5, :3].mean() < 30:
            mask = (arr[:, :, 0] > 25) | (arr[:, :, 1] > 25) | (arr[:, :, 2] > 25)
            rows = np.where(mask.any(axis=1))[0]
            cols = np.where(mask.any(axis=0))[0]
            if len(rows) and len(cols):
                im = im.crop((cols[0], rows[0], cols[-1] + 1, rows[-1] + 1))
                arr = np.array(im)
                h, w = arr.shape[:2]
                
        # 2. Xử lý nền trắng bên ngoài biên bằng FloodFill có chọn lọc
        if (arr[:, :, 3] < 250).sum() < 100:
            corners = [arr[0, 0, :3], arr[0, w-1, :3], arr[h-1, 0, :3], arr[h-1, w-1, :3]]
            if any(c.mean() > 225 for c in corners):
                bgr = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2BGR)
                flood_mask = np.zeros((h + 2, w + 2), np.uint8)
                seeds = [(0, 0), (w-1, 0), (0, h-1), (w-1, h-1), (0, h//2), (w-1, h//2), (w//2, 0), (w//2, h-1)]
                for sx, sy in seeds:
                    if bgr[sy, sx].mean() > 220:
                        cv2.floodFill(
                            bgr.copy(), flood_mask, (sx, sy), 
                            (0, 0, 0), (18, 18, 18), (18, 18, 18), 
                            flags=4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8)
                        )
                ext_bg_mask = (flood_mask[1:h+1, 1:w+1] == 255)
                arr[:, :, 3][ext_bg_mask] = 0
                im = Image.fromarray(arr, mode="RGBA")
                bbox = im.getbbox()
                if bbox:
                    im = im.crop(bbox)
                    
        return im

    def enhance_sharpness_and_clarity(self, prod_rgba: Image.Image, sharpness_boost: float = 1.8) -> Image.Image:
        """
        Bộ lọc AI Super-Resolution & Edge Contrast Unsharp Masking chuyên dụng cho ảnh sản phẩm / sách scan:
        - Tự động khử nhiễu vi hạt bằng cv2.bilateralFilter giữ nguyên sắc cạnh viền.
        - Khôi phục độ sắc nét và tương phản cục bộ của chữ (Typography clarity) bằng Unsharp Masking & cv2.detailEnhance.
        - Giúp văn bản, hoa văn, logo và bìa sách đạt độ nét căng bóng thương mại ngay cả khi nguồn vào là thumbnail độ phân giải thấp (250px).
        """
        import cv2
        import numpy as np

        if sharpness_boost <= 1.0:
            return ImageEnhance.Sharpness(prod_rgba).enhance(sharpness_boost)

        # Tách kênh màu RGB và Alpha
        rgba = prod_rgba.convert("RGBA")
        r, g, b, a = rgba.split()
        rgb_img = Image.merge("RGB", (r, g, b))
        
        # Chuyển đổi sang BGR cho OpenCV
        bgr = cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2BGR)

        # 1. Khử nhiễu hạt nền nhưng bảo toàn triệt để cạnh sắc
        denoised = cv2.bilateralFilter(bgr, d=5, sigmaColor=35, sigmaSpace=35)

        # 2. Unsharp Masking tăng cường tần số cao (High-pass boost cho chữ và chi tiết)
        # Hệ số weight tăng dần theo sharpness_boost (ví dụ boost=1.8 -> weight=2.2)
        weight = float(np.clip(1.0 + (sharpness_boost - 1.0) * 1.5, 1.2, 2.8))
        neg_weight = -(weight - 1.0)
        gaussian = cv2.GaussianBlur(denoised, (0, 0), sigmaX=2.5)
        unsharp = cv2.addWeighted(denoised, weight, gaussian, neg_weight, 0)

        # 3. Tăng cường chi tiết vi cấu trúc chữ bằng cv2.detailEnhance
        try:
            enhanced_cv = cv2.detailEnhance(unsharp, sigma_s=8, sigma_r=0.18)
        except Exception:
            enhanced_cv = unsharp

        # Chuyển lại về Pillow RGB
        rgb_enhanced = cv2.cvtColor(enhanced_cv, cv2.COLOR_BGR2RGB)
        pil_enhanced = Image.fromarray(rgb_enhanced)

        # 4. Tinh chỉnh nhẹ độ tương phản và độ nét Pillow
        pil_enhanced = ImageEnhance.Contrast(pil_enhanced).enhance(1.08)
        pil_enhanced = ImageEnhance.Sharpness(pil_enhanced).enhance(min(2.0, 1.0 + (sharpness_boost - 1.0) * 0.4))

        # Ghép lại với kênh Alpha gốc
        enhanced_rgba = pil_enhanced.convert("RGBA")
        enhanced_rgba.putalpha(a)
        return enhanced_rgba

    def render_3d_product_mockup(self, prod_img: Image.Image, target_height: int = 540) -> Image.Image:
        """Tách nền thông minh và tăng cường khối 2.5D cho máy móc thiết bị."""
        prod = prod_img.convert("RGBA")
        datas = prod.getdata()
        new_data = []
        for item in datas:
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        prod.putdata(new_data)
        
        orig_w, orig_h = prod.size
        aspect = orig_w / orig_h
        target_w = int(target_height * aspect)
        prod = prod.resize((target_w, target_height), Image.Resampling.LANCZOS)
        prod = ImageEnhance.Sharpness(prod).enhance(1.2)
        bbox = prod.getbbox()
        return prod.crop(bbox) if bbox else prod

    def generate_studio_mockup_ai(
        self,
        sku: str,
        product_name: str,
        brand: str = "AATCC",
        category: str = "Manual",
        style: str = "branded_studio",
        api_key: Optional[str] = None
    ) -> Optional[Path]:
        """
        Tạo ảnh Mockup 3D Studio thương mại cao cấp bằng Google Gemini / Imagen AI.
        Hỗ trợ cả Gemini Developer API (Google AI Studio Key) và Vertex AI Enterprise mode.
        LOẠI BỎ HOÀN TOÀN việc ghép ảnh 2D chắp vá bằng OpenCV.
        """
        from gemini_studio import edit_studio
        from media_quality import safe_name
        source = self.get_product_image_for_sku(sku)
        backgrounds = self.get_backgrounds()
        if not source or not backgrounds:
            raise ValueError("Cần chọn ảnh nguồn và nền trước khi chỉnh sửa AI")
        preview = self.preview_dir / f"{safe_name(sku)}_preview.png"
        result = edit_studio(source, backgrounds[0], preview, sku)
        self.manifest[sku] = dict(result, sku=sku)
        self._save_manifest()
        return preview

    def generate_studio_mockup_cloud_free(self, *args, **kwargs):
        raise ValueError("Tạo ảnh từ tên không xác minh được sản phẩm. Hãy chọn ảnh nguồn và dùng chỉnh sửa theo ảnh tham chiếu.")

    def composite_product_image(
        self, 
        sku: str, 
        product_img_path: Path, 
        bg_path: Optional[Path] = None, 
        render_mode: str = "branded_3d",
        horizon_y: int = 550,
        depth_ratio: float = 0.20,
        shadow_density: float = 0.80,
        enable_reflection: bool = True,
        sharpness_boost: float = 1.8
    ) -> Path:
        """
        AI Ghép nền Studio chuẩn thương mại điện tử (chuẩn như catalogue quốc tế):
        - Tự động nhận diện BIS_BACKGROUND.png là phông nền 3D studio gốc đạt chuẩn.
        - Tự động loại bỏ viền đen/viền trắng bao quanh sản phẩm.
        - Đặt sản phẩm lớn nổi bật (chiếm 68-72% khung hình), vững vàng trên mặt sàn.
        - Đổ bóng vật lý 2 lớp: Bóng tiếp xúc chân đế (Ambient Occlusion) + Bóng tỏa mềm + Phản xạ mờ mặt sàn.
        """
        from media_quality import studio_draft, safe_name
        clean_sku = safe_name(sku)
        if bg_path is None:
            backgrounds = self.get_backgrounds()
            if not backgrounds:
                raise ValueError("Cần chọn phông nền")
            bg_path = backgrounds[0]
        preview = self.preview_dir / f"{clean_sku}_preview.png"
        report = studio_draft(product_img_path, bg_path, preview, remove_white=False)
        self.manifest[clean_sku] = dict(report, sku=clean_sku, preview_image=str(preview))
        self._save_manifest()
        return preview

    def register_final_composite(self, sku: str, image_bytes: bytes) -> Path:
        """Lưu trực tiếp ảnh mockup thành phẩm từ Canva/Photoroom và đưa vào cổng duyệt."""
        from media_quality import checked_image, safe_name
        image = checked_image(image_bytes)
        if image.size != (1254,1254):
            raise ValueError("Ảnh thành phẩm cần đúng 1254×1254")
        target = self.preview_dir / f"{safe_name(sku)}_preview.png"
        image.convert("RGB").save(target, format="PNG")
        self.manifest[sku] = {"sku":sku, "status":"PENDING_REVIEW", "preview_image":str(target)}
        self._save_manifest()
        return target

    def approve_image(self, sku, source_override=None):
        from media_quality import safe_name
        import hashlib, shutil
        entry = self.manifest.get(sku,{})
        source = Path(source_override or entry.get("preview_image") or self.preview_dir/f"{safe_name(sku)}_preview.png")
        if not source.is_file():
            return False
        with Image.open(source) as image:
            if image.size != (1254,1254):
                return False
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        target = self.final_dir / f"{safe_name(sku)}_approved_{digest[:12]}{source.suffix}"
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        entry.update(sku=sku, status="APPROVED", final_image=str(target), approved_sha256=digest,
                     approved_at=time.strftime("%Y-%m-%d %H:%M:%S"))
        self.manifest[sku]=entry
        self._save_manifest()
        return True

    def reject_image(self, sku, reason=""):
        # Keep approved files and benchmarks intact; only update review state.
        if sku not in self.manifest:
            return False
        self.manifest[sku].update(status="REJECTED", reject_reason=reason)
        self._save_manifest()
        return True

    def process_product_image(self, sku: str, images: list, bg_path: Path = None) -> dict:
        """Process and composite product images with default or selected background."""
        if not images:
            return {"sku": sku, "status": "NO_IMAGES", "composite_path": None}
        
        if bg_path is None or not Path(bg_path).exists():
            bg_list = self.get_backgrounds()
            bg_path = bg_list[0] if bg_list else (self.bg_dir / "modern_textile_lab.jpg")

        first_img = Path(images[0])
        final_path = self.composite_product_image(sku, first_img, Path(bg_path))
        return {
            "sku": sku,
            "status": "PENDING_REVIEW",
            "composite_path": str(final_path),
            "background": str(bg_path)
        }


    def extract_all_images_from_pdf(
        self,
        pdf_path: str | Path,
        output_dir: Optional[Path] = None,
        min_width: int = 250,
        min_height: int = 250
    ) -> List[Dict[str, Any]]:
        """
        Trích xuất toàn bộ ảnh nhúng nguyên bản (raw embedded) chất lượng cao từ file PDF Catalogue:
        - Lọc bỏ icon rác/đường kẻ nhỏ theo ngưỡng min_width và min_height (mặc định > 250px).
        - Khử trùng lặp ảnh (Deduplication) theo mã băm MD5.
        - Trả về danh sách metadata và lưu vào thư mục Raw_Catalog_Extracted.
        """
        import pymupdf
        import hashlib

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return []

        if output_dir is None:
            output_dir = self.gdrive_storage / "4_Product_Images" / "Raw_Catalog_Extracted" / pdf_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)

        doc = pymupdf.open(str(pdf_path))
        extracted_list = []
        seen_hashes = set()
        img_idx_counter = 0

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            for img in page.get_images(full=True):
                xref = img[0]
                base_image = doc.extract_image(xref)
                w, h = base_image.get("width", 0), base_image.get("height", 0)
                image_bytes = base_image.get("image", b"")
                ext = base_image.get("ext", "jpg")

                if w >= min_width and h >= min_height and image_bytes:
                    img_hash = hashlib.md5(image_bytes).hexdigest()
                    if img_hash in seen_hashes:
                        continue
                    seen_hashes.add(img_hash)

                    img_idx_counter += 1
                    file_name = f"page_{page_idx+1:02d}_img_{img_idx_counter:03d}_{w}x{h}.{ext}"
                    out_file = output_dir / file_name

                    with open(out_file, "wb") as f_out:
                        f_out.write(image_bytes)

                    extracted_list.append({
                        "file_name": file_name,
                        "path": str(out_file),
                        "page": page_idx + 1,
                        "width": w,
                        "height": h,
                        "size_kb": round(len(image_bytes) / 1024, 1),
                        "format": ext.upper()
                    })

        return extracted_list

    def smart_media_pipeline(
        self,
        sku: str,
        product_name: str = "",
        brand: str = "",
        pdf_path: Optional[str | Path] = None,
        page_num: int = 1,
        bg_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Quy trình xử lý ảnh Media Studio thuần Google Drive:
        1. Tìm kiếm ảnh do người dùng đặt vào Google_Drive_Storage/4_Product_Images/ trùng với mã SKU.
        2. Ghép vào Mockup nền Studio/Lab chân thực với bóng đổ và cân chỉnh ánh sáng 2K.
        """
        clean_sku = sku.strip().replace(" ", "_")
        source_img = self.get_product_image_for_sku(clean_sku)

        composite_res = None
        if source_img and source_img.exists():
            if bg_path is None or not Path(bg_path).exists():
                bg_list = self.get_backgrounds()
                bg_path = bg_list[0] if bg_list else (self.bg_dir / "modern_textile_lab.jpg")

            final_path = self.composite_product_image(clean_sku, source_img, Path(bg_path))
            composite_res = str(final_path)

        return {
            "sku": clean_sku,
            "source_type": f"GOOGLE_DRIVE ({source_img.name})" if source_img else "NONE",
            "raw_brand_image": str(source_img) if source_img else None,
            "composite_image": composite_res,
            "status": "READY_FOR_APPROVAL" if composite_res else "NEEDS_IMAGE"
        }
