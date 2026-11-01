import os
import requests
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Tự động nạp cấu hình từ .env nếu có
load_dotenv()

# Lấy token từ biến môi trường hoặc nhập trực tiếp từ https://chatgpt.com/api/auth/session
CHATGPT_ACCESS_TOKEN = (
    os.environ.get("CHATGPT_ACCESS_TOKEN") 
    or "your-chatgpt-access-token-here"
)

CHAT2API_BASE_URL = os.environ.get("CHAT2API_BASE_URL") or "http://localhost:8080/v1"

def check_chat2api_server(base_url: str) -> bool:
    """Kiểm tra xem proxy Chat2API cục bộ có đang chạy hay không."""
    import socket
    import urllib.parse
    parsed = urllib.parse.urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8080
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        res = s.connect_ex((host, port))
        s.close()
        return res == 0
    except Exception:
        return False

def test_chat2api_image(sku: str, prompt_text: str):
    print("=" * 65)
    print(f"🚀 KIỂM THỬ PHƯƠNG ÁN 2: CHAT2API (DALL-E 3 QUA REVERSE PROXY)")
    print("=" * 65)
    print(f"Target Server: {CHAT2API_BASE_URL}")
    print(f"SKU: {sku}")

    # 1. Kiểm tra trạng thái server proxy
    if not check_chat2api_server(CHAT2API_BASE_URL):
        print(f"\n❌ [CẢNH BÁO] Không tìm thấy server Chat2API đang lắng nghe trên {CHAT2API_BASE_URL}!")
        print("\n👉 CÁCH KHỞI ĐỘNG CHAT2API SERVER:")
        print("   Cách 1 (Dùng Python trực tiếp):")
        print("      git clone https://github.com/LanQian528/chat2api")
        print("      cd chat2api")
        print("      pip install -r requirements.txt")
        print("      python app.py")
        print("   Cách 2 (Dùng Docker 1 dòng lệnh):")
        print("      docker run -d -p 8080:8080 --name chat2api lanqian528/chat2api:latest")
        print("\n👉 CÁCH LẤY ACCESS TOKEN CHATGPT WEB:")
        print("   1. Mở trình duyệt Chrome đã đăng nhập tài khoản ChatGPT.")
        print("   2. Truy cập: https://chatgpt.com/api/auth/session")
        print("   3. Sao chép toàn bộ chuỗi 'accessToken' và dán vào file .env:")
        print("      CHATGPT_ACCESS_TOKEN=\"eyJhbGciOi...\"")
        print("=" * 65)
        return False

    if not CHATGPT_ACCESS_TOKEN or "your-chatgpt" in CHATGPT_ACCESS_TOKEN:
        print("\n⚠️ Vui lòng cung cấp CHATGPT_ACCESS_TOKEN hợp lệ lấy từ https://chatgpt.com/api/auth/session")
        return False

    # 2. Khởi tạo OpenAI Client trỏ về Proxy Chat2API
    client = OpenAI(
        api_key=CHATGPT_ACCESS_TOKEN,
        base_url=CHAT2API_BASE_URL
    )

    print(f"\n⏳ Đang gửi lệnh sinh ảnh DALL-E 3 tới ChatGPT Reverse Proxy...")
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt_text,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        img_url = response.data[0].url
        print(f"✓ Đã nhận URL ảnh từ ChatGPT: {img_url[:60]}...")
        
        # Tải ảnh về lưu máy
        r = requests.get(img_url, timeout=30)
        if r.status_code == 200:
            out_path = Path(f"test_chatgpt_{sku}.jpg")
            with open(out_path, "wb") as f:
                f.write(r.content)
            print(f"✓ HOÀN TẤT THÀNH CÔNG! Ảnh đã lưu tại: {out_path.resolve()} ({len(r.content):,} bytes)")
            return True
        else:
            print(f"❌ Không thể tải ảnh từ URL: HTTP {r.status_code}")
            return False

    except Exception as e:
        print(f"\n❌ Lỗi gọi Chat2API: {e}")
        print("💡 Lưu ý: Tài khoản ChatGPT Web gói Free có thể bị giới hạn hạn mức DALL-E 3 hoặc bị Cloudflare Challenge.")
        return False

if __name__ == "__main__":
    prompt = (
        "Commercial 3D studio product shot of the technical reference book "
        "'AATCC Manual of International Test Methods and Procedures'. "
        "Hardcover binding, standing firmly at a natural 15-degree perspective on a clean white reflective studio floor. "
        "Soft contact shadows beneath the book, even studio lighting, sharp 4K catalog quality, raytraced reflection."
    )
    test_chat2api_image("03026A", prompt)
