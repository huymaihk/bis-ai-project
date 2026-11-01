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
        import pymupdf
        clean_sku = sku.strip().replace(" ", "_")
        target_path = self.brand_dir / f"{clean_sku}_brand_1.jpg"

        # Kiểm tra xem sản phẩm có phải tài liệu/tiêu chuẩn/sổ tay không
        name_lower = (product_name or "").lower()
        is_book_or_standard = any(k in name_lower for k in [
            "manual", "standard", "tiêu chuẩn", "tieu chuan", "book", "sách", "aatcc", "iso", "astm"
        ])

        # 1. Thử bóc trực tiếp từ đúng trang page_num
        exact_page_imgs = self.extract_images_from_exact_page(pdf_path, page_num)
        # Chỉ nhận ảnh thực sự có dung lượng > 5KB (5000 bytes) để tránh lấy icon nhỏ hoặc viền
        valid_page_imgs = [img for img in exact_page_imgs if img.get("size_bytes", 0) > 5000]

        if valid_page_imgs:
            best_img = valid_page_imgs[0]
            with open(target_path, "wb") as f:
                f.write(best_img["image_bytes"])
            print(f"✓ Đã trích ảnh {clean_sku} chuẩn xác từ trang {page_num} ({best_img['width']}x{best_img['height']}, {best_img['size_bytes']:,} bytes)")
            return target_path

        # Nếu là sách / tiêu chuẩn mà trang PDF không có ảnh bìa > 5KB:
        # Ngừng ngay lập tức, trả về None để hệ thống chuyển sang tìm ảnh Web (tránh bóc nhầm máy móc/tủ sấy ở trang khác)
        if is_book_or_standard:
            print(f"ℹ️ Sản phẩm '{sku}' là sách/tiêu chuẩn ({product_name}) - Không tìm thấy ảnh bìa > 5KB trên trang {page_num}. Chuyển sang tìm kiếm Web.")
            return None

        # 2. Với thiết bị máy móc thông thường: nếu trang không có ảnh và cho phép scan_all:
        if scan_all:
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
            if os.path.exists(str(pdf_path)):
                try:
                    doc = pymupdf.open(str(pdf_path))
                    sku_clean_lower = sku.strip().lower()
                    for p_idx in range(len(doc)):
                        if p_idx == page_num - 1:
                            continue
                        txt = doc[p_idx].get_text().lower()
                        if sku_clean_lower in txt:
                            sku_page_imgs = self.extract_images_from_exact_page(pdf_path, p_idx + 1)
                            valid_sku_imgs = [img for img in sku_page_imgs if img.get("size_bytes", 0) > 5000]
                            if valid_sku_imgs:
                                best_img = valid_sku_imgs[0]
                                with open(target_path, "wb") as f:
                                    f.write(best_img["image_bytes"])
                                print(f"✓ Tìm thấy {clean_sku} tại trang {p_idx + 1} qua quét SKU text ({best_img['size_bytes']:,} bytes)")
                                doc.close()
                                return target_path
                    doc.close()
                except Exception as e:
                    print(f"Error scanning PDF: {e}")

        # ❌ XÓA BỎ HOÀN TOÀN ĐOẠN CHỤP NGUYÊN TRANG BÌA (FALLBACK BITMAP) CŨ!
        # Nếu không có ảnh thiết bị hoặc sách thực tế trong PDF, trả về None để hệ thống chuyển sang tìm Web
        print(f"⚠️ Không tìm thấy ảnh sản phẩm hợp lệ (> 5KB) cho SKU {clean_sku} trong file PDF này.")
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
        if not query:
            return ""
        clean_q = self.clean_search_query(query)
        words = clean_q.strip().split()
        stop_words = {"of", "and", "the", "for", "procedures", "methods", "hardbound", "book", "standard", "test", "-", ":"}
        clean_words = [w for w in words if w.lower() not in stop_words]

        if len(clean_words) >= 4:
            return " ".join(clean_words[:4])
        elif clean_words:
            return " ".join(clean_words)
        return clean_q.strip()

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
                    if any(bad in title or bad in img_url or bad in domain for bad in blacklist):
                        continue

                    raw_img = r.get("image")
                    if raw_img:
                        results.append({
                            "image_url": raw_img,
                            "thumb_url": r.get("thumbnail") or raw_img,
                            "title": r.get("title", short_query),
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
        clean_sku = sku.strip().replace(" ", "_")
        target_path = self.brand_dir / f"{clean_sku}_brand_{index}.jpg"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        try:
            try:
                from curl_cffi import requests as http_client
                r = http_client.get(image_url, headers=headers, impersonate="chrome", timeout=20)
            except ImportError:
                import requests as http_client
                r = http_client.get(image_url, headers=headers, timeout=20)
            if r.status_code == 200 and len(r.content) > 1500:
                with open(target_path, "wb") as f:
                    f.write(r.content)
                print(f"✓ Đã lưu ảnh sản phẩm {clean_sku} ({len(r.content):,} bytes) từ {image_url}")
                return target_path
        except Exception as e:
            print(f"Error downloading image from {image_url}: {e}")
        return None

    def fetch_brand_image_from_web(self, sku: str, brand_name: str, title: str, product_name_vi: str = "") -> Optional[Path]:
        """
        Tìm và lưu ảnh sản phẩm thực tế từ Web kết hợp thông minh:
        - Tên hãng (Brand) + Mã SKU + Tên sản phẩm tiếng Anh / tiếng Việt.
        """
        clean_sku = sku.strip().replace(" ", "_")
        
        # Tạo danh sách các truy vấn theo độ ưu tiên từ cụ thể nhất đến tổng quát
        queries = []
        if title:
            queries.append(f"{brand_name} {sku} {title}".strip())
        queries.append(f"{brand_name} {sku}".strip())
        if product_name_vi and product_name_vi != title:
            queries.append(f"{brand_name} {sku} {product_name_vi}".strip())
        if title:
            queries.append(f"{brand_name} {title}".strip())

        for q in queries:
            results = self.search_web_images(q, max_results=5)
            for res in results:
                saved = self.download_and_save_brand_image(clean_sku, res["image_url"])
                if saved and saved.exists():
                    return saved

        # Fallback phụ: thử cào trang web thương hiệu trực tiếp
        try:
            from brand_web_enricher import resolve_brand_domain, fetch_brand_product_page
            domain = resolve_brand_domain(brand_name)
            web_data = fetch_brand_product_page(domain, sku, title)
            if web_data and web_data.get("images"):
                for img_url in web_data["images"]:
                    saved = self.download_and_save_brand_image(clean_sku, img_url)
                    if saved and saved.exists():
                        return saved
        except Exception as e:
            print(f"Error in brand domain fallback: {e}")

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
        clean_sku = sku.strip().replace(" ", "_")
        preview_target = self.preview_dir / f"{clean_sku}_preview.jpg"
        
        # 1. Khởi tạo Google GenAI SDK
        from google import genai
        from google.genai import types
        import config

        active_key = (
            api_key 
            or os.environ.get("GEMINI_API_KEY") 
            or getattr(config, "GEMINI_API_KEY", "")
        )
        if not active_key or len(str(active_key).strip()) < 10:
            raise ValueError("Chưa cấu hình GEMINI_API_KEY hợp lệ. Vui lòng kiểm tra file config.py hoặc ô nhập API Key.")

        # 2. Xây dựng Prompt nhiếp ảnh thương mại chuẩn Studio cao cấp
        name_lower = product_name.lower()
        is_book = any(w in name_lower for w in ["manual", "book", "sách", "tiêu chuẩn", "standard", "guide", "tập san", "tài liệu"])
        
        if is_book:
            prompt_subject = (
                f"A luxury commercial 3D product mockup of the official hardcover technical book titled '{product_name}' "
                f"(Model/SKU: {sku}) published by '{brand}'. "
                f"The book stands upright in three-quarter perspective on a clean, luxury reflective studio tabletop. "
                f"Ultra-detailed hardcover with crisp typography, sharp gold embossed lettering of the title, "
                f"pristine straight book spine and realistic fine paper texture on page edges. "
            )
        else:
            prompt_subject = (
                f"Photorealistic 3D commercial studio product photography of high-precision textile testing instrument '{product_name}' "
                f"(Model/SKU: {sku}) manufactured by '{brand}'. "
                f"The device is placed on a pristine reflective laboratory workbench. "
                f"Ultra-high precision industrial design, crisp metallic dials, clear digital display screen, immaculate product finish with model '{sku}' clearly marked. "
            )

        full_prompt = (
            f"{prompt_subject} "
            f"The scene is illuminated by balanced, soft studio softbox lighting. "
            f"Natural soft contact drop shadow underneath, subtle reflection on the table surface, ultra-sharp focus on details, "
            f"4K resolution, hyper-realistic, commercial catalog aesthetic, no distortion, no watermarks, perfectly centered."
        )

        client = genai.Client(api_key=str(active_key).strip())
        img_bytes = None

        # 3. Điều hướng gọi phương thức phù hợp theo chế độ API
        try:
            # Nếu chạy ở chế độ Vertex AI (Enterprise)
            if getattr(getattr(client, "_api_client", None), "vertexai", False):
                print(f"[AgentMedia] Đang gọi Imagen 3 qua Vertex AI cho SKU {clean_sku}...")
                result = client.models.generate_images(
                    model='imagen-3.0-generate-002',
                    prompt=full_prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="1:1"
                    )
                )
                if result and hasattr(result, "generated_images") and result.generated_images:
                    img_bytes = result.generated_images[0].image.image_bytes
            else:
                # Chế độ Gemini Developer API (Google AI Studio Key AQ...)
                print(f"[AgentMedia] Đang gọi Google Developer Image API cho SKU {clean_sku}...")
                image_models_to_try = [
                    "gemini-2.5-flash-image",
                    "gemini-3.1-flash-image",
                    "gemini-3-pro-image"
                ]
                last_err = None
                for m_name in image_models_to_try:
                    try:
                        resp = client.models.generate_content(
                            model=m_name,
                            contents=full_prompt,
                            config=types.GenerateContentConfig(
                                response_modalities=["IMAGE"]
                            )
                        )
                        if resp.candidates and resp.candidates[0].content and resp.candidates[0].content.parts:
                            for part in resp.candidates[0].content.parts:
                                if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                                    raw_data = part.inline_data.data
                                    if isinstance(raw_data, str):
                                        import base64
                                        img_bytes = base64.b64decode(raw_data)
                                    else:
                                        img_bytes = raw_data
                                    break
                        if img_bytes:
                            break
                    except Exception as ex_m:
                        last_err = ex_m
                        err_str = str(ex_m)
                        if "RESOURCE_EXHAUSTED" in err_str or "limit: 0" in err_str:
                            raise RuntimeError(
                                "Tài khoản Google AI Studio của bạn đang ở gói Free Tier (Google quy định hạn mức tạo ảnh AI là 0 lượt/ngày trên gói miễn phí, chỉ miễn phí các model văn bản). "
                                "Để kích hoạt tạo ảnh AI, bạn cần bật Pay-as-you-go (gắn thẻ thanh toán) tại https://aistudio.google.com/app/plan_information "
                                "hoặc sử dụng nút 'Tùy chọn Studio Ngoài (Canva)' ngay bên dưới để tạo mockup miễn phí."
                            )
                        continue

                if not img_bytes and last_err:
                    raise last_err

            if img_bytes and len(img_bytes) > 1000:
                with open(preview_target, "wb") as f:
                    f.write(img_bytes)

                # Cập nhật manifest trạng thái PENDING_REVIEW chờ duyệt
                self.manifest[clean_sku] = {
                    "sku": clean_sku,
                    "status": "PENDING_REVIEW",
                    "source": "GEMINI_IMAGEN3_AI",
                    "render_mode": "Gemini AI Studio",
                    "preview_image": str(preview_target),
                    "prompt": full_prompt,
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self._save_manifest()
                print(f"✓ Đã tạo thành công ảnh 3D Studio qua Gemini AI: {preview_target} ({len(img_bytes):,} bytes)")
                return preview_target
            else:
                raise RuntimeError("Không nhận được dữ liệu hình ảnh từ Google AI Studio API.")

        except Exception as e:
            print(f"❌ [AgentMedia] Lỗi gọi Google Image API: {e}")
            raise e




    def generate_studio_mockup_cloud_free(
        self,
        sku: str,
        product_name: str,
        brand: str = "AATCC"
    ) -> Optional[Path]:
        """
        Tạo ảnh Mockup 3D Studio thương mại cao cấp hoàn toàn MIỄN PHÍ qua Cloud Serverless.
        Không cần GPU rời (chạy ngay trên Intel Iris Xe), không yêu cầu API Key hay liên kết thẻ.
        """
        import urllib.parse
        import requests
        clean_sku = sku.strip().replace(" ", "_")
        preview_target = self.preview_dir / f"{clean_sku}_preview.jpg"
        
        name_lower = product_name.lower()
        is_book = any(w in name_lower for w in ["manual", "book", "sách", "tiêu chuẩn", "standard", "guide", "tập san", "tài liệu"])
        
        if is_book:
            prompt = (
                f"Commercial 3D studio product shot of the technical reference book '{product_name}' (Code: {sku}) published by '{brand}'. "
                f"Hardcover binding, standing firmly at a natural 15-degree perspective on a clean white reflective studio floor. "
                f"Soft contact shadows beneath the book, even studio lighting, sharp 4K catalog quality, raytraced reflection."
            )
        else:
            prompt = (
                f"Commercial 3D studio product shot of precision textile testing instrument '{product_name}' (Model: {sku}) by '{brand}'. "
                f"Standing on a clean white reflective laboratory workbench. Soft contact drop shadow, bright studio softbox lighting, 4K UHD catalog quality."
            )

        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?seed=42"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

        print(f"[AgentMedia] Đang kết nối Cloud AI Serverless miễn phí cho SKU {clean_sku}...")
        res = requests.get(url, headers=headers, timeout=60)
        if res.status_code == 200 and len(res.content) > 5000:
            with open(preview_target, "wb") as f:
                f.write(res.content)

            self.manifest[clean_sku] = {
                "sku": clean_sku,
                "status": "PENDING_REVIEW",
                "source": "CLOUD_AI_SERVERLESS",
                "render_mode": "Cloud AI Studio (Free)",
                "preview_image": str(preview_target),
                "prompt": prompt,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self._save_manifest()
            print(f"✓ Đã tạo thành công ảnh 3D Studio qua Cloud AI: {preview_target} ({len(res.content):,} bytes)")
            return preview_target
        else:
            raise RuntimeError(f"Cloud AI Serverless trả về mã HTTP {res.status_code}")

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
        clean_sku = sku.strip().replace(" ", "_")
        final_path = self.final_dir / f"{clean_sku}_final.jpg"
        preview_path = self.preview_dir / f"{clean_sku}_preview.jpg"

        # 1. Chuẩn bị ảnh phông nền
        if bg_path is None or not Path(bg_path).exists():
            bg_list = self.get_backgrounds()
            bg_path = bg_list[0] if bg_list else (self.bg_dir / "BIS_BACKGROUND.png")
            
        bg_path = Path(bg_path)
        is_bis_bg = "BIS_BACKGROUND" in bg_path.name
        is_prerendered_bg = is_bis_bg or "modern_textile_lab" in bg_path.name or "luxury_marble_podium" in bg_path.name or "clean_studio" in bg_path.name

        if is_prerendered_bg:
            # Dùng trực tiếp phông nền studio 3D đạt chuẩn độ nét cao, không bị warp biến dạng
            bg_img = Image.open(bg_path).convert("RGBA").resize((1024, 1024), Image.Resampling.LANCZOS)
            ground_baseline = 850 if is_bis_bg else 690
        else:
            # Nếu người dùng tải lên mẫu hoa văn 2D phẳng riêng thì mới dựng phối cảnh tường - sàn
            bg_img = self.create_3d_branded_backdrop(
                pattern_img_path=bg_path,
                canvas_w=1024,
                canvas_h=1024,
                horizon_y=horizon_y,
                depth_ratio=depth_ratio
            )
            ground_baseline = min(960, horizon_y + int((1024 - horizon_y) * 0.72))

        # 2. Tiền xử lý sản phẩm: Loại bỏ viền đen / viền trắng
        raw_prod = Image.open(product_img_path)
        prod_rgba = self.smart_prepare_product(raw_prod)

        # 3. Dựng khối và co giãn kích thước nổi bật (Tỷ lệ chuẩn 68-72% khung hình như Hanna & MQuant)
        if render_mode == "book_3d":
            rendered_obj = self.render_3d_book_mockup(prod_rgba, target_height=680)
        elif render_mode == "product_25d":
            rendered_obj = self.render_3d_product_mockup(prod_rgba, target_height=700)
        else:
            # Chế độ branded_3d hoặc flat_2d: Giữ nguyên form thực tế của sản phẩm
            target_h = 700
            target_w = int(prod_rgba.size[0] * (target_h / prod_rgba.size[1]))
            if target_w > 800:
                target_w = 800
                target_h = int(prod_rgba.size[1] * (target_w / prod_rgba.size[0]))
            rendered_obj = prod_rgba.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # Tăng cường độ nét AI Super-Resolution & tương phản viền chữ
        if sharpness_boost > 1.0:
            rendered_obj = self.enhance_sharpness_and_clarity(rendered_obj, sharpness_boost=sharpness_boost)

        obj_w, obj_h = rendered_obj.size
        pos_x = (1024 - obj_w) // 2
        pos_y = ground_baseline - obj_h

        # 4. Áp dụng hệ thống đổ bóng vật lý 2 lớp chân thực
        composed = self.apply_realistic_contact_shadow(
            backdrop=bg_img,
            prod_rgba=rendered_obj,
            pos_x=pos_x,
            pos_y=pos_y,
            shadow_density=shadow_density,
            enable_reflection=enable_reflection
        )

        # 5. Tinh chỉnh màu sắc và độ sắc nét hoàn thiện
        enhancer = ImageEnhance.Sharpness(composed.convert("RGB"))
        final_img = enhancer.enhance(1.15)
        color_enhancer = ImageEnhance.Color(final_img)
        final_img = color_enhancer.enhance(1.05)

        final_img.save(preview_path, quality=95)

        # Ghi nhận trạng thái PENDING_REVIEW
        self.manifest[clean_sku] = {
            "sku": clean_sku,
            "status": "PENDING_REVIEW",
            "render_mode": render_mode,
            "background": bg_path.name,
            "horizon_y": horizon_y,
            "depth_ratio": depth_ratio,
            "shadow_density": shadow_density,
            "sharpness_boost": sharpness_boost,
            "preview_image": str(preview_path),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save_manifest()
        return preview_path

    def register_final_composite(self, sku: str, image_bytes: bytes) -> Path:
        """Lưu trực tiếp ảnh mockup thành phẩm từ Canva/Photoroom và đưa vào cổng duyệt."""
        clean_sku = sku.strip().replace(" ", "_")
        final_path = self.final_dir / f"{clean_sku}_final.jpg"
        preview_path = self.preview_dir / f"{clean_sku}_preview.jpg"
        with open(final_path, "wb") as f:
            f.write(image_bytes)
        self.manifest[clean_sku] = {
            "sku": clean_sku,
            "status": "APPROVED",
            "source": "EXTERNAL_MOCKUP (Canva/Photoroom)",
            "final_image": str(final_path),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save_manifest()
        return final_path

    def approve_image(self, sku: str, source_override: Optional[Path] = None) -> bool:
        """
        Chinh thuc PHE DUYET anh san pham:
        - Chi khi nguoi dung bam DUYET thi anh moi duoc luu chinh thuc vao 6_Final_Composites.
        - Tu dong dong bo sang Google Drive may tinh.
        - Danh dau trang thai APPROVED trong manifest cho Haravan sync.
        """
        import shutil
        clean_sku = sku.strip().replace(" ", "_")
        preview_path = self.preview_dir / f"{clean_sku}_preview.jpg"
        final_path = self.final_dir / f"{clean_sku}_final.jpg"

        src_to_save = None
        if source_override and Path(source_override).exists():
            src_to_save = Path(source_override)
        elif preview_path.exists():
            src_to_save = preview_path

        if src_to_save and src_to_save.exists():
            shutil.copy2(src_to_save, final_path)

        # Dong bo truc tiep sang Google Drive may tinh
        alt_gdrive = Path(r"g:\My Drive\BIS_AI_PROJECT\Google_Drive_Storage\6_Final_Composites")
        if alt_gdrive.exists() and alt_gdrive.resolve() != self.final_dir.resolve() and final_path.exists():
            try:
                shutil.copy2(final_path, alt_gdrive / final_path.name)
            except Exception:
                pass

        if clean_sku in self.manifest:
            self.manifest[clean_sku]["status"] = "APPROVED"
            self.manifest[clean_sku]["final_image"] = str(final_path)
            self.manifest[clean_sku]["approved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.manifest[clean_sku] = {
                "sku": clean_sku,
                "status": "APPROVED",
                "final_image": str(final_path),
                "approved_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        self._save_manifest()
        return True

    def reject_image(self, sku: str, reason: str = "") -> bool:
        """
        Tu choi anh: Xoa anh khoi 6_Final_Composites de khong bao gio luu nham anh chua duyet.
        """
        clean_sku = sku.strip().replace(" ", "_")
        final_path = self.final_dir / f"{clean_sku}_final.jpg"
        if final_path.exists():
            try:
                final_path.unlink()
            except Exception:
                pass
        alt_gdrive = Path(r"g:\My Drive\BIS_AI_PROJECT\Google_Drive_Storage\6_Final_Composites") / f"{clean_sku}_final.jpg"
        if alt_gdrive.exists():
            try:
                alt_gdrive.unlink()
            except Exception:
                pass

        if clean_sku in self.manifest:
            self.manifest[clean_sku]["status"] = "REJECTED"
            self.manifest[clean_sku]["reject_reason"] = reason
            self.manifest[clean_sku]["final_image"] = None
            self._save_manifest()
            return True
        return False

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
