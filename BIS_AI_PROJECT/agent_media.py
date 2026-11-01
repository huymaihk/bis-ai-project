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
        - BƯỚC 1: Quét chính xác trang `page_num` (source_page). Nếu trang có ảnh, lấy ảnh nét nhất trên ĐÚNG TRANG ĐÓ.
        - BƯỚC 2: Chỉ khi trang đó hoàn toàn không có ảnh và scan_all=True thì mới quét các trang khác chứa đúng mã SKU.
        - Tuyệt đối không lấy ảnh lung tung từ các trang khác khi trang hiện tại đã có ảnh.
        """
        import pymupdf
        clean_sku = sku.strip().replace(" ", "_")
        target_path = self.brand_dir / f"{clean_sku}_brand_1.jpg"

        # 1. Thử bóc trực tiếp từ đúng trang page_num
        exact_page_imgs = self.extract_images_from_exact_page(pdf_path, page_num)
        if exact_page_imgs:
            best_img = exact_page_imgs[0]
            with open(target_path, "wb") as f:
                f.write(best_img["image_bytes"])
            print(f"✓ Đã trích ảnh {clean_sku} chuẩn xác từ trang {page_num} ({best_img['width']}x{best_img['height']}, {best_img['size_bytes']:,} bytes)")
            return target_path

        # 2. Nếu trang đó không có ảnh và cho phép scan_all: chỉ quét trang có chứa đúng mã SKU
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
                            if sku_page_imgs:
                                best_img = sku_page_imgs[0]
                                with open(target_path, "wb") as f:
                                    f.write(best_img["image_bytes"])
                                print(f"✓ Tìm thấy {clean_sku} tại trang {p_idx + 1} qua quét SKU text")
                                doc.close()
                                return target_path
                    doc.close()
                except Exception as e:
                    print(f"Error scanning PDF: {e}")

        # 3. Fallback chụp bitmap trang nếu vẫn không có ảnh
        try:
            doc = pymupdf.open(str(pdf_path))
            fallback_p = page_num - 1 if 1 <= page_num <= len(doc) else 0
            pix = doc[fallback_p].get_pixmap(matrix=pymupdf.Matrix(1.8, 1.8))
            pix.save(str(target_path))
            print(f"⚠️ Fallback: Chụp nguyên trang {fallback_p + 1} làm ảnh cho {clean_sku}")
            doc.close()
            return target_path
        except Exception:
            pass

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

    def search_duckduckgo_images(self, query: str, max_results: int = 8) -> list[dict]:
        """
        Tìm kiếm ảnh sản phẩm chất lượng cao, chuẩn như Google qua DuckDuckGo (ddgs).
        Hoàn toàn miễn phí, không dính banner quảng cáo Bing Cashback/Rewards.
        """
        clean_q = self.clean_search_query(query)
        if not clean_q:
            return []

        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                try:
                    ddgs_gen = ddgs.images(
                        query=clean_q,
                        region="wt-wt",
                        safesearch="off",
                        max_results=max_results
                    )
                except TypeError:
                    ddgs_gen = ddgs.images(
                        keywords=clean_q,
                        region="wt-wt",
                        safesearch="off",
                        max_results=max_results
                    )

                results = []
                for r in ddgs_gen:
                    img_url = r.get("image")
                    if img_url:
                        results.append({
                            "image_url": img_url,
                            "thumb_url": r.get("thumbnail") or img_url,
                            "title": r.get("title", clean_q),
                            "domain": r.get("source") or "DuckDuckGo"
                        })
                    if len(results) >= max_results:
                        break

                if results:
                    print(f"✓ Đã tìm thấy {len(results)} ảnh sạch qua DuckDuckGo cho '{clean_q}'")
                    return results
        except Exception as e:
            print(f"Lỗi tìm kiếm ảnh qua DDGS: {e}")
        return []

    def search_bing_async_images(self, query: str, max_results: int = 8) -> list[dict]:
        """
        Tìm kiếm qua Bing Images Async API làm giải pháp dự phòng thứ 3:
        - Khử trùng lặp từ khóa.
        - Lọc bỏ triệt để các thẻ ads/cashback/coupon/rewards.
        """
        import urllib.parse
        import json
        import re

        clean_q = self.clean_search_query(query)
        if not clean_q:
            return []

        use_cffi = False
        try:
            from curl_cffi import requests as cffi_requests
            use_cffi = True
        except ImportError:
            import requests as cffi_requests

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            BeautifulSoup = None

        encoded = urllib.parse.quote_plus(clean_q)
        url = f"https://www.bing.com/images/async?q={encoded}&first=0&count=30&mmasync=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,vi;q=0.8"
        }

        bad_domains = [
            "bing.com", "microsoft.com", "onmsft.com", "pcmag.com", "notebooks.com",
            "coupon", "cashback", "rakuten", "slickdeals", "retailmenot"
        ]
        bad_keywords = [
            "reward", "cashback", "coupon", "discount", "deal", "promo", "gift card", "voucher"
        ]

        results = []
        try:
            if use_cffi:
                session = cffi_requests.Session(impersonate="chrome")
                r = session.get(url, headers=headers, timeout=15)
            else:
                r = cffi_requests.get(url, headers=headers, timeout=15)

            if r.status_code == 200:
                html_text = r.text
                if BeautifulSoup:
                    soup = BeautifulSoup(html_text, "html.parser")
                    for a in soup.find_all("a", class_="iusc"):
                        m_attr = a.get("m")
                        if not m_attr:
                            continue
                        try:
                            m_data = json.loads(m_attr)
                            murl = m_data.get("murl")
                            turl = m_data.get("turl")
                            desc = m_data.get("desc", "")
                            purl = m_data.get("purl", "")
                            if not murl:
                                continue

                            domain = re.sub(r"https?://(www\.)?", "", purl or murl).split("/")[0].lower()
                            if any(bd in domain for bd in bad_domains):
                                continue
                            if any(bk in desc.lower() for bk in bad_keywords):
                                continue

                            if not any(skip in murl.lower() for skip in ["logo", "icon", "banner", "avatar", "favicon", "pixel"]):
                                results.append({
                                    "image_url": murl,
                                    "thumb_url": turl or murl,
                                    "title": desc or clean_q,
                                    "domain": domain
                                })
                                if len(results) >= max_results:
                                    break
                        except Exception:
                            continue
        except Exception as e:
            print(f"Error searching Bing async images: {e}")
        return results

    def search_web_images(self, query: str, max_results: int = 8) -> list[dict]:
        """
        Công cụ tìm kiếm ảnh đa tầng (Multi-tier Image Search Engine):
        1. Ưu tiên 1 (Chính thống): Google Custom Search API (nếu được cấu hình API Key & CX).
        2. Ưu tiên 2 (Mặc định miễn phí): DuckDuckGo Images DDGS (trả về kết quả sạch chuẩn như Google, 0% quảng cáo).
        3. Dự phòng 3: Bing Images Async API lọc sạch Ads.
        """
        # 1. Thử Google Custom Search API nếu có cấu hình
        google_results = self.search_google_custom_search(query, max_results=max_results)
        if google_results:
            return google_results

        # 2. Thử DuckDuckGo Images (DDGS) - Sạch 100%, không dính quảng cáo Bing
        ddg_results = self.search_duckduckgo_images(query, max_results=max_results)
        if ddg_results:
            return ddg_results

        # 3. Dự phòng Bing Async đã lọc sạch Ads
        bing_results = self.search_bing_async_images(query, max_results=max_results)
        if bing_results:
            return bing_results

        return []

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
        Kiến trúc kết hợp thông minh 3 bước cho AI Agent Media Studio:
        1. Ưu tiên 1 (Nội tại): Dùng PyMuPDF quét trang PDF chứa sản phẩm lấy ảnh gốc độ nét cao nhất.
        2. Dự phòng (Fallback): Nếu không tìm thấy hoặc ảnh dưới 250px -> Tự động tìm bổ sung ảnh Web (Bing/DuckDuckGo) theo Brand + SKU + Tên SP.
        3. Hậu xử lý (Composite): Ghép ảnh sản phẩm vào bối cảnh Mockup Studio/Lab dệt may chân thực.
        """
        clean_sku = sku.strip().replace(" ", "_")
        target_brand_img = self.brand_dir / f"{clean_sku}_brand_1.jpg"
        source_type = "NONE"

        # Bước 1: Ưu tiên bóc tách từ PDF
        if pdf_path and Path(pdf_path).exists():
            extracted = self.extract_image_from_pdf(clean_sku, pdf_path, page_num, product_name)
            if extracted and extracted.exists() and extracted.stat().st_size > 8000:
                source_type = "PDF_EMBEDDED"

        # Bước 2: Fallback tìm ảnh Web nếu chưa có ảnh
        if not target_brand_img.exists() or source_type == "NONE":
            query = f"{brand} {clean_sku} {product_name}".strip()
            web_results = self.search_web_images(query, max_results=5)
            if web_results:
                top_img = web_results[0]
                dl_path = self.download_and_save_brand_image(clean_sku, top_img["image_url"], index=1)
                if dl_path and dl_path.exists():
                    source_type = f"WEB_SEARCH ({top_img.get('domain', 'Web')})"

        # Bước 3: Ghép vào mockup nền Studio/Lab
        composite_res = None
        if target_brand_img.exists():
            if bg_path is None or not Path(bg_path).exists():
                bg_list = self.get_backgrounds()
                bg_path = bg_list[0] if bg_list else (self.bg_dir / "modern_textile_lab.jpg")

            final_path = self.composite_product_image(clean_sku, target_brand_img, Path(bg_path))
            composite_res = str(final_path)

        return {
            "sku": clean_sku,
            "source_type": source_type,
            "raw_brand_image": str(target_brand_img) if target_brand_img.exists() else None,
            "composite_image": composite_res,
            "status": "READY_FOR_APPROVAL" if composite_res else "NEEDS_IMAGE"
        }
