"""
BIS Textile Pipeline - Brand Official Website Enricher
Bypasses Cloudflare using curl_cffi Chrome impersonation to directly retrieve
official product specifications, high-res images, and role evidence from brand websites.
Complies with BIS Textile legacy rules (Tab 14 - Nguồn Bổ Sung Có Chứng Cứ).
"""
import os
import sys
import json
import time
import re
from pathlib import Path
from urllib.parse import quote_plus

from curl_cffi import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL, PRODUCT_COLUMNS

# ── Brand Official Domains Registry ───────────────────────────────────────────
BRAND_DOMAINS = {
    "AATCC": "aatcc.org",
    "SDC": "sdc.org.uk",
    "SDL ATLAS": "sdlatlas.com",
    "JAMES HEAL": "james-heal.co.uk",
    "TESTFABRICS": "testfabrics.com",
    "Q-LAB": "q-lab.com",
    "VERIVIDE": "verivide.com",
    "ROACHES": "roaches.co.uk",
    "DATACOLOR": "datacolor.com",
    "X-RITE": "xrite.com",
}


def resolve_brand_domain(brand_name: str, project_dir: Path | None = None) -> str:
    """Resolve brand official domain from registry or Links.txt."""
    if project_dir:
        links_file = project_dir / "Links.txt"
        if links_file.exists():
            with open(links_file, "r", encoding="utf-8") as f:
                for line in f:
                    url = line.strip()
                    if url.startswith("http"):
                        domain = re.sub(r"https?://(www\.)?", "", url).split("/")[0]
                        print(f"  ✓ Found official domain in Links.txt: {domain}")
                        return domain

    brand_upper = brand_name.upper().strip()
    for k, domain in BRAND_DOMAINS.items():
        if k in brand_upper:
            return domain

    return "aatcc.org"


def fetch_brand_product_page(brand_domain: str, sku: str, title_query: str = "") -> dict | None:
    """
    Search and fetch the official brand web page for a given SKU using curl_cffi (impersonating Chrome).
    Bypasses Cloudflare turnstile and bot protection.
    """
    queries = [sku]
    if title_query and len(title_query) > 5:
        # Also try searching by key terms in title
        queries.append(re.sub(r"[^\w\s]", "", title_query)[:40])

    for query in queries:
        search_url = f"https://www.{brand_domain}/?s={quote_plus(query)}"
        try:
            resp = requests.get(search_url, impersonate="chrome", timeout=20)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Look for matching articles, news, or product links
                target_url = None
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    text = a.get_text().strip().lower()
                    if brand_domain in href:
                        if sku.lower() in href.lower() or (title_query and any(w.lower() in text for w in title_query.split()[:3])):
                            target_url = href
                            break

                # If found specific subpage, fetch it
                if target_url and target_url != search_url:
                    page_resp = requests.get(target_url, impersonate="chrome", timeout=20)
                    if page_resp.status_code == 200:
                        soup = BeautifulSoup(page_resp.text, "html.parser")
                else:
                    target_url = search_url

                # Extract readable text
                paragraphs = [p.get_text().strip() for p in soup.find_all(["p", "h1", "h2", "h3", "li", "td"]) if len(p.get_text().strip()) > 20]
                text_content = " ".join(paragraphs)[:4000]

                # Extract product images
                img_urls = []
                for img in soup.find_all("img", src=True):
                    src = img["src"]
                    if any(ext in src.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                        if not any(skip in src.lower() for skip in ["logo", "icon", "banner", "avatar"]):
                            if src.startswith("//"):
                                src = "https:" + src
                            elif src.startswith("/"):
                                src = f"https://www.{brand_domain}" + src
                            if src not in img_urls:
                                img_urls.append(src)

                if text_content:
                    return {
                        "source_url": target_url,
                        "domain": brand_domain,
                        "text_snippet": text_content,
                        "images": img_urls[:3],
                    }

        except Exception as e:
            print(f"  ⚠ Brand fetch error for '{query}': {e}")
            continue

    return None


def enrich_facts_with_gemini(client: genai.Client, raw_product: dict, web_data: dict) -> dict:
    """Use Gemini to cross-verify and extract official facts from the brand web page."""
    prompt = f"""
Bạn là chuyên gia thẩm định dữ liệu sản phẩm của BIS Textile (Module Nguồn Bổ Sung Có Chứng Cứ - Tab 14).

SẢN PHẨM HIỆN CÓ TỪ CATALOGUE:
- Mã SKU: {raw_product.get('sku')}
- Tên tiếng Việt: {raw_product.get('product_name')}
- Tên tiếng Anh: {raw_product.get('product_name_en')}

NỘI DUNG TỪ TRANG WEB CHÍNH THỨC CỦA HÃNG ({web_data.get('domain')} - {web_data.get('source_url')}):
\"\"\"{web_data.get('text_snippet')[:3000]}\"\"\"

NHIỆM VỤ:
1. Xác định xem nội dung web hãng có liên quan hoặc trực tiếp đề cập đến sản phẩm này không.
2. Trích xuất các thông tin bổ sung chính hãng:
   - official_english_title: Tên chuẩn hãng niêm yết
   - verified_role: Xác định rõ vai trò của {web_data.get('domain')} (VD: "Nhà xuất bản tiêu chuẩn quốc tế" hay "Nhà sản xuất thiết bị kiểm nghiệm")
   - evidence_quote: Một câu trích dẫn nguyên văn từ web hãng chứng minh thông tin trên

Chỉ trả về JSON thuần túy (không markdown fences):
{{
  "is_match": true,
  "official_english_title": "...",
  "verified_role": "...",
  "evidence_quote": "..."
}}
"""
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=2048,
                response_mime_type="application/json",
            ),
        )
        data = json.loads(response.text.strip())
        return data
    except Exception as e:
        print(f"  ⚠ Gemini web fact extraction error: {e}")
        return {}


def enrich_product(client: genai.Client, product: dict, brand_name: str = "AATCC") -> dict:
    """Enrich a single product with official brand web data."""
    sku = product.get("sku")
    domain = resolve_brand_domain(brand_name)
    title_query = product.get("product_name_en") or product.get("product_name") or ""

    print(f"\n🌐 Tra cứu trang hãng {domain} cho SKU: {sku} …")
    web_data = fetch_brand_product_page(domain, sku, title_query)
    if not web_data or not web_data.get("text_snippet"):
        print(f"  ⏭ Không tìm thấy trang chi tiết trên {domain}")
        return product

    facts = enrich_facts_with_gemini(client, product, web_data)

    if facts.get("is_match"):
        print(f"  ✓ Đã khớp với dữ liệu chính hãng: {facts.get('official_english_title')}")
        if web_data.get("images") and not product.get("image_urls"):
            product["image_urls"] = ",".join(web_data["images"])
            print(f"  ✓ Bổ sung {len(web_data['images'])} ảnh chính hãng")

        if facts.get("official_english_title"):
            product["product_name_en"] = facts["official_english_title"]

        notes = product.get("notes") or ""
        evidence_tag = (
            f"\n[NGUỒN WEB HÃNG XÁC THỰC: {web_data['source_url']}]\n"
            f"Vai trò tổ chức: {facts.get('verified_role')}\n"
            f"Trích dẫn: \"{facts.get('evidence_quote')}\""
        )
        product["notes"] = (notes + evidence_tag).strip()
        print(f"  ✓ Đã ghi chứng cứ nguồn web vào hồ sơ kỹ thuật (Audit B5 PASS)")

    return product
