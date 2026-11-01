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
        self.gdrive_storage = self.workspace_dir / "Google_Drive_Storage"
        self.gdrive_storage.mkdir(parents=True, exist_ok=True)
        
        # Thư mục hình ảnh lưu trữ trực tiếp trên Google Drive
        self.brand_dir = self.gdrive_storage / "4_Product_Images"
        self.user_dir = self.gdrive_storage / "4_Product_Images"
        self.bg_dir = self.gdrive_storage / "5_Studio_Backgrounds"
        self.final_dir = self.gdrive_storage / "6_Final_Composites"
        
        for d in [self.brand_dir, self.user_dir, self.bg_dir, self.final_dir]:
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

    def composite_product_image(
        self, 
        sku: str, 
        product_img_path: Path, 
        bg_path: Path, 
        render_mode: str = "book_3d"
    ) -> Path:
        """
        AI Ghép nền Studio với hệ thống bóng đổ 3 tầng (Contact Shadow, Cast Shadow, Ambient Shadow):
        - render_mode == 'book_3d': Dựng sách 3D có gáy sách, độ dày trang và góc nghiêng 3D.
        - render_mode == 'product_25d': Tách nền và đổ bóng tiếp xúc cho máy móc/thiết bị.
        - render_mode == 'flat_2d': Giữ nguyên ảnh phẳng 2D.
        """
        clean_sku = sku.strip().replace(" ", "_")
        final_path = self.final_dir / f"{clean_sku}_final.jpg"

        bg_img = Image.open(bg_path).convert("RGBA").resize((1000, 1000), Image.Resampling.LANCZOS)
        raw_prod = Image.open(product_img_path)

        # 1. Dựng vật thể theo chế độ đã chọn
        if render_mode == "book_3d":
            rendered_obj = self.render_3d_book_mockup(raw_prod, target_height=490)
        elif render_mode == "product_25d":
            rendered_obj = self.render_3d_product_mockup(raw_prod, target_height=520)
        else:
            rendered_obj = raw_prod.convert("RGBA")
            rendered_obj.thumbnail((650, 650), Image.Resampling.LANCZOS)

        obj_w, obj_h = rendered_obj.size
        # Đặt vật thể đứng trên mặt bàn / bục podium (chân chạm tại y = 690)
        pos_x = (1000 - obj_w) // 2
        pos_y = 690 - obj_h

        # 2. Tạo hệ thống bóng đổ 3 tầng siêu thực (3-Tier Photorealistic Shadow)
        # Tầng 1: Contact Shadow (Bóng tiếp xúc tối sát đáy, dẹp sát chân vật thể)
        contact_shadow = Image.new("RGBA", (1000, 1000), (0, 0, 0, 0))
        cs_draw = ImageDraw.Draw(contact_shadow)
        cs_box = [pos_x + 10, 685, pos_x + obj_w - 10, 702]
        cs_draw.ellipse(cs_box, fill=(10, 15, 25, 240))
        contact_shadow = contact_shadow.filter(ImageFilter.GaussianBlur(3))

        # Tầng 2: Cast Shadow (Bóng đổ lan tỏa theo hướng ánh sáng)
        cast_shadow = Image.new("RGBA", (1000, 1000), (0, 0, 0, 0))
        cast_draw = ImageDraw.Draw(cast_shadow)
        cast_box = [pos_x - 10, 678, pos_x + obj_w + 50, 725]
        cast_draw.ellipse(cast_box, fill=(20, 30, 45, 140))
        cast_shadow = cast_shadow.filter(ImageFilter.GaussianBlur(14))

        # Tầng 3: Ambient Shadow (Bóng mờ khuếch tán diện rộng)
        amb_shadow = Image.new("RGBA", (1000, 1000), (0, 0, 0, 0))
        amb_draw = ImageDraw.Draw(amb_shadow)
        amb_box = [pos_x - 40, 670, pos_x + obj_w + 80, 745]
        amb_draw.ellipse(amb_box, fill=(30, 45, 65, 80))
        amb_shadow = amb_shadow.filter(ImageFilter.GaussianBlur(25))

        # 3. Ghép các tầng: Nền -> Ambient -> Cast -> Contact -> Sản phẩm
        composed = Image.alpha_composite(bg_img, amb_shadow)
        composed = Image.alpha_composite(composed, cast_shadow)
        composed = Image.alpha_composite(composed, contact_shadow)
        composed.paste(rendered_obj, (pos_x, pos_y), rendered_obj)

        # 4. Tinh chỉnh màu sắc và độ sắc nét hoàn thiện
        enhancer = ImageEnhance.Sharpness(composed.convert("RGB"))
        final_img = enhancer.enhance(1.15)
        color_enhancer = ImageEnhance.Color(final_img)
        final_img = color_enhancer.enhance(1.05)

        final_img.save(final_path, quality=95)

        # Ghi nhận trạng thái PENDING_REVIEW
        self.manifest[clean_sku] = {
            "sku": clean_sku,
            "status": "PENDING_REVIEW",
            "render_mode": render_mode,
            "background": bg_path.name,
            "final_image": str(final_path),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save_manifest()
        return final_path

    def register_final_composite(self, sku: str, image_bytes: bytes) -> Path:
        """Lưu trực tiếp ảnh mockup thành phẩm từ Canva/Photoroom và đưa vào cổng duyệt."""
        clean_sku = sku.strip().replace(" ", "_")
        final_path = self.final_dir / f"{clean_sku}_final.jpg"
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
