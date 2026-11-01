import urllib.parse
import requests
from pathlib import Path

def test_pollinations_flux(sku: str, prompt_text: str):
    print(f"⏳ Đang tạo ảnh qua Cloud AI cho SKU {sku} (Không cần GPU, chạy trực tiếp trên Intel Iris Xe)...")
    encoded_prompt = urllib.parse.quote(prompt_text)
    
    # URL serverless miễn phí 100% không yêu cầu API key
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed=42"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    print(f"👉 Đang kết nối Cloud AI Serverless...")
    res = requests.get(url, headers=headers, timeout=60)
    
    if res.status_code == 200 and len(res.content) > 5000:
        out_path = Path(f"test_cloud_{sku}.jpg")
        with open(out_path, "wb") as f:
            f.write(res.content)
        print(f"✓ Hoàn tất thành công! Đã tạo ảnh Studio 3D chân thực.")
        print(f"📁 Vị trí file: {out_path.resolve()} ({len(res.content):,} bytes)")
        return out_path
    else:
        print(f"❌ Lỗi HTTP: {res.status_code} ({len(res.content)} bytes)")
        return None

if __name__ == "__main__":
    prompt = (
        "Commercial 3D studio product shot of the technical reference book "
        "'AATCC Manual of International Test Methods and Procedures'. "
        "Hardcover binding, standing firmly at a natural 15-degree perspective on a clean white reflective studio floor. "
        "Soft contact shadows beneath the book, even studio lighting, sharp 4K catalog quality, raytraced reflection."
    )
    test_pollinations_flux("03026A", prompt)
