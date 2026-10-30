"""
BIS Textile AI - Agent Marketing (SEO & Content Research Department)
Responsible for:
- Textile SEO keyword research (AATCC, ISO, ASTM, Fabric Testing, QA/QC Lab)
- Bilingual SEO Meta Title, Meta Description, URL Slug generation
- Commercial e-commerce product pitch, Value propositions & Buyer persona targeting
- Social media snippets / Google Search Snippet preview
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from google import genai

from config import GEMINI_API_KEY, GEMINI_MODEL

class AgentMarketing:
    def __init__(self, workspace_dir: str | Path | None = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path(__file__).parent.resolve()
        self.cache_dir = self.workspace_dir / "marketing_cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate_seo_package(self, product: dict) -> dict:
        """
        Generate full SEO & Content package for a product.
        Includes:
        - Meta Title (< 60 chars)
        - Meta Description (150-160 chars)
        - Friendly URL Slug
        - Primary & Secondary SEO Keywords
        - E-commerce Selling Pitch (Lý do chọn mua)
        - Google Search Preview
        """
        sku = product.get("sku", "")
        name_vi = product.get("product_name", "")
        name_en = product.get("product_name_en", "")
        desc = product.get("description", "")
        category = product.get("category", "Tài liệu tiêu chuẩn")
        brand = product.get("brand_evidence", "AATCC (Hoa Kỳ)")

        cache_path = self.cache_dir / f"seo_{sku}.json"
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        prompt = f"""Bạn là Trưởng phòng SEO & Marketing của BIS Textile Việt Nam (nhà cung cấp thiết bị, tài liệu thử nghiệm dệt may hàng đầu).
Hãy lập kế hoạch SEO và nội dung bán hàng cho sản phẩm sau:

Mã SKU: {sku}
Tên tiếng Việt: {name_vi}
Tên tiếng Anh: {name_en}
Danh mục: {category}
Hãng sản xuất / Tổ chức: {brand}
Mô tả kỹ thuật: {desc}

Yêu cầu xuất ra JSON chính xác theo cấu trúc:
{{
  "meta_title": "Tiêu đề SEO ngắn gọn dưới 60 ký tự kèm mã {sku} và thương hiệu BIS Textile",
  "meta_description": "Mô tả SEO hấp dẫn từ 150-160 ký tự, chứa từ khóa chính, thúc đẩy click xem chi tiết",
  "url_slug": "slug-than-thien-khong-dau-co-sku",
  "focus_keywords": ["Từ khóa chính 1", "Từ khóa chính 2", "Từ khóa 3"],
  "secondary_keywords": ["Từ khóa ngách 1", "Từ khóa ngách 2"],
  "selling_points": [
    "Điểm bán hàng nổi bật 1 (Lợi ích cho phòng lab QA/QC)",
    "Điểm bán hàng nổi bật 2 (Độ tin cậy chính hãng có CO/CQ)",
    "Điểm bán hàng nổi bật 3 (Hỗ trợ kỹ thuật chuyên sâu từ BIS)"
  ],
  "target_audience": "Đối tượng khách hàng mục tiêu (ví dụ: Nhà máy dệt nhuộm, Phòng kiểm nghiệm dệt may, Chuyên viên QA/QC)"
}}
Chỉ trả về JSON thuần túy, không có thẻ markdown ```json.
"""
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
            raw = response.text.strip()
            if raw.startswith("```json"): raw = raw[7:]
            if raw.startswith("```"): raw = raw[3:]
            if raw.endswith("```"): raw = raw[:-3]
            data = json.loads(raw.strip())
        except Exception as e:
            # Fallback nếu API bận
            slug = name_en.lower().replace(" ", "-").replace("/", "-")
            slug = "".join(c for c in slug if c.isalnum() or c == "-")[:50]
            data = {
                "meta_title": f"{name_vi} ({sku}) | BIS Textile Việt Nam",
                "meta_description": f"Phân phối chính hãng {name_vi} mã {sku} từ {brand}. Tiêu chuẩn kiểm nghiệm dệt may quốc tế, đầy đủ CO/CQ và hỗ trợ kỹ thuật tại BIS Textile.",
                "url_slug": f"{slug}-{sku.lower()}",
                "focus_keywords": [name_vi, sku, f"tiêu chuẩn {brand}", "kiểm nghiệm dệt may"],
                "secondary_keywords": ["AATCC manual", "tài liệu QA dệt may", "BIS Textile"],
                "selling_points": [
                    "Ấn bản chính hãng chuẩn hóa quốc tế mới nhất",
                    "Đầy đủ chứng từ nguồn gốc CO/CQ và hóa đơn VAT",
                    "Tư vấn kỹ thuật kiểm nghiệm phòng lab chuyên sâu từ BIS Textile"
                ],
                "target_audience": "Trưởng phòng QA/QC dệt may, Kỹ thuật viên phòng thí nghiệm, Nhà máy may xuất khẩu"
            }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return data

    def load_marketing_knowledge(self) -> dict:
        """Đọc tri thức nghiên cứu thị trường & SEO đã học được từ file cache."""
        know_file = self.workspace_dir / "marketing_knowledge.json"
        if know_file.exists():
            try:
                with open(know_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def research_industry_websites(self) -> dict:
        """
        Nghiên cứu và học hỏi phong cách trình bày nội dung Haravan và website ngành:
        1. https://bistextile.com/collections/all
        2. https://qclabtex.com/
        3. https://labgartex.com/
        4. https://bisvn.net/
        -> Trích xuất cấu trúc trình bày, thẻ tiêu đề, bảng thông số kỹ thuật, từ khóa SEO ngành dệt may.
        -> Nạp tri thức vào marketing_knowledge.json và đồng bộ vào feedback_memory.json cho toàn bộ AI tự học!
        """
        import requests
        from bs4 import BeautifulSoup
        import urllib3
        urllib3.disable_warnings()

        target_urls = [
            {"name": "bistextile.com (Chủ quản BIS)", "url": "https://bistextile.com/collections/all"},
            {"name": "qclabtex.com (Thiết bị kiểm nghiệm QC)", "url": "https://qclabtex.com/"},
            {"name": "labgartex.com (Thiết bị phòng lab dệt may)", "url": "https://labgartex.com/"},
            {"name": "bisvn.net (Hệ sinh thái BIS VN)", "url": "https://bisvn.net/"}
        ]

        scraped_data = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        print("\n🌐 [Agent_Marketing] Bắt đầu quét và nghiên cứu 4 website đối chuẩn ngành...")
        for target in target_urls:
            name = target["name"]
            url = target["url"]
            try:
                r = requests.get(url, headers=headers, timeout=12, verify=False)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    title = soup.title.string.strip() if soup.title and soup.title.string else ""
                    h1s = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)][:5]
                    h2s = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)][:10]
                    p_texts = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 25][:8]
                    scraped_data.append({
                        "site": name,
                        "url": url,
                        "title": title,
                        "headings": h1s + h2s,
                        "sample_snippets": p_texts
                    })
                    print(f"  ✓ Đã thu thập dữ liệu từ {url} ({len(h1s + h2s)} tiêu đề, {len(p_texts)} đoạn mẫu)")
                else:
                    print(f"  ⚠ {url} trả về mã {r.status_code}")
            except Exception as e:
                print(f"  ⚠ Lỗi kết nối {url}: {e}")

        # Dùng Gemini AI phân tích cấu trúc, văn phong và từ khóa SEO chuẩn
        prompt = f"""Bạn là Giám đốc Marketing & SEO chuyên sâu ngành thiết bị và vật tư kiểm nghiệm dệt may tại Việt Nam.
Dưới đây là dữ liệu thực tế thu thập từ 4 website hàng đầu ngành dệt may:
1. bistextile.com (Nền tảng thương mại điện tử Haravan của BIS Textile)
2. qclabtex.com (Chuyên thiết bị đo lường & vật tư thử nghiệm vải)
3. labgartex.com (Thiết bị phòng thí nghiệm dệt may, may mặc)
4. bisvn.net (Nhà cung cấp giải pháp sợi, vải, dệt nhuộm)

Dữ liệu thô thu thập được:
{json.dumps(scraped_data, ensure_ascii=False, indent=2)}

Hãy phân tích toàn diện và đúc kết thành Bộ Tri Thức Chuẩn Hóa Trình Bày Nội Dung & Chiến Lược SEO cho BIS Textile theo cấu trúc JSON:
{{
  "analyzed_sites": ["bistextile.com", "qclabtex.com", "labgartex.com", "bisvn.net"],
  "presentation_style_rules": [
    "Quy tắc 1: Cách đặt tiêu đề sản phẩm chuẩn B2B dệt may (kèm mã SKU, tên tiếng Anh, chuẩn áp dụng)",
    "Quy tắc 2: Cấu trúc mô tả kỹ thuật (phân tách rõ nguyên lý hoạt động, phạm vi áp dụng, tiêu chuẩn thử nghiệm)",
    "Quy tắc 3: Bảng thông số kỹ thuật (thiết kế 2 cột tỷ lệ 39%-61%, rõ ràng nguồn điện, kích thước, tải trọng, độ chính xác)",
    "Quy tắc 4: Khối cam kết chứng chỉ & nguồn gốc (CO, CQ, hóa đơn VAT, hỗ trợ hiệu chuẩn phòng lab)",
    "Quy tắc 5: Nút kêu gọi hành động (CTA) và tài liệu tra cứu đính kèm"
  ],
  "top_seo_keywords": [
    "thiết bị kiểm nghiệm dệt may", "vật tư thử nghiệm dệt may", "tiêu chuẩn AATCC", "độ bền màu vải",
    "máy đo độ bền ma sát", "tủ so màu vải", "thang xám AATCC", "tiêu chuẩn ISO 105", "phòng lab QA QC dệt may"
  ],
  "haravan_layout_blueprint": {{
    "font_family": "Segoe UI, -apple-system, sans-serif",
    "color_palette": {{
      "primary": "#0284c7",
      "heading": "#0f172a",
      "body": "#334155",
      "border": "#cbd5e1",
      "background_highlight": "#f0f9ff"
    }},
    "block_structure": [
      "Khối 1: Tên tiếng Việt in đậm 20px chuẩn SEO",
      "Khối 2: Tên tiếng Anh 15px chuẩn hóa quốc tế",
      "Khối 3: Hãng sản xuất, xuất xứ và đơn vị phân phối chính ngạch",
      "Khối 4: Giới thiệu ứng dụng thực tế phòng lab",
      "Khối 5: Đặc điểm nổi bật (3-5 gạch đầu dòng lợi ích)",
      "Khối 6: Bảng thông số kỹ thuật 2 cột chuẩn 39%-61%",
      "Khối 7: Tài liệu tiêu chuẩn và link tra cứu chính hãng"
    ]
  }},
  "learned_business_rules": [
    "Luôn ghi rõ tổ chức tiêu chuẩn (AATCC, ISO, ASTM, GB, DIN, JIS) trong tiêu đề và mô tả",
    "Bảng thông số kỹ thuật bắt buộc có đơn vị tính, phạm vi áp dụng và trang nguồn trong Catalogue",
    "Không đưa giá bán cố định đối với thiết bị nhập khẩu, thay bằng chính sách báo giá chính hãng kèm hỗ trợ kỹ thuật",
    "Đính kèm liên kết tra cứu tài liệu chính thống để nâng cao uy tín thẩm định"
  ]
}}
Chỉ trả về JSON thuần túy, không có thẻ markdown ```json.
"""
        knowledge_res = {}
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )
            raw = response.text.strip()
            if raw.startswith("```json"): raw = raw[7:]
            if raw.startswith("```"): raw = raw[3:]
            if raw.endswith("```"): raw = raw[:-3]
            knowledge_res = json.loads(raw.strip())
        except Exception as e:
            print(f"  ⚠ Lỗi gọi Gemini tổng hợp tri thức ({e}), sử dụng mẫu phân tích chuẩn...")
            knowledge_res = {
                "analyzed_sites": ["bistextile.com", "qclabtex.com", "labgartex.com", "bisvn.net"],
                "presentation_style_rules": [
                    "Tiêu đề chuẩn song ngữ: [Tên tiếng Việt chuẩn ngành] - [Tên tiếng Anh theo tài liệu hãng] ([Mã SKU])",
                    "Khối giới thiệu: Nhấn mạnh công năng kiểm tra độ bền màu, độ mài mòn, độ xù lông hoặc độ bền kéo vải",
                    "Đặc điểm nổi bật: Liệt kê các tiêu chuẩn tương thích (AATCC, ISO 105, ASTM, GB/T, JIS L)",
                    "Bảng thông số: Tỷ lệ 39% thuộc tính và 61% giá trị chi tiết, rõ ràng xuất xứ và quy cách đóng gói",
                    "Cam kết phân phối: Cung cấp chính ngạch bởi BIS Textile Việt Nam, đầy đủ CO/CQ và hóa đơn VAT"
                ],
                "top_seo_keywords": [
                    "thiết bị kiểm nghiệm dệt may", "vật tư thử nghiệm vải", "tiêu chuẩn AATCC", "độ bền màu",
                    "tủ so màu vải", "thang xám chuyển màu", "vải thử độ bền ma sát", "tiêu chuẩn ISO 105", "BIS Textile"
                ],
                "haravan_layout_blueprint": {
                    "font_family": "Segoe UI, sans-serif",
                    "block_structure": [
                        "Khối 1: Tên tiếng Việt chuẩn ngành",
                        "Khối 2: Tên tiếng Anh đối chuẩn",
                        "Khối 3: Hãng xuất xứ & Đơn vị phân phối",
                        "Khối 4: Giới thiệu súc tích nguyên lý",
                        "Khối 5: Đặc điểm nổi bật",
                        "Khối 6: Bảng thông số 2 cột chuẩn 39%-61%",
                        "Khối 7: Tài liệu & Tiêu chuẩn tra cứu liên quan"
                    ]
                },
                "learned_business_rules": [
                    "Luôn ghi rõ tổ chức tiêu chuẩn (AATCC, ISO, ASTM) trong tiêu đề và mô tả",
                    "Bảng thông số kỹ thuật bắt buộc có đơn vị tính, phạm vi áp dụng và trang nguồn",
                    "Cung cấp chính ngạch bởi BIS Textile kèm hỗ trợ kỹ thuật chuyên sâu"
                ]
            }

        # Lưu lại tri thức nghiên cứu vào marketing_knowledge.json
        know_file = self.workspace_dir / "marketing_knowledge.json"
        with open(know_file, "w", encoding="utf-8") as f:
            json.dump(knowledge_res, f, ensure_ascii=False, indent=2)

        # Tự động nạp các quy tắc học được vào feedback_memory.json của hệ thống
        from learning_engine import LearningEngine
        le = LearningEngine(self.workspace_dir)
        for r in knowledge_res.get("learned_business_rules", []):
            le.add_custom_rule(r)

        print(f"✓ [Agent_Marketing] Đã nạp thành công bộ tri thức từ 4 website và bổ sung vào Learning Engine!")
        return knowledge_res

