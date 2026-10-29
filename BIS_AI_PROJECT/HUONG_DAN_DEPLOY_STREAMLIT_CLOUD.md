# 🚀 HƯỚNG DẪN TRIỂN KHAI HỆ THỐNG BIS AI CHẠY 24/7 TRÊN STREAMLIT CLOUD (MIỄN PHÍ)

Hệ thống sau khi triển khai sẽ chạy độc lập trên máy chủ đám mây, **tắt máy tính hệ thống vẫn hoạt động 24/7**, bất kỳ ai có mã PIN đều có thể truy cập qua điện thoại hoặc máy tính từ xa.

---

### BƯỚC 1: TẠO KHO LƯU TRỮ TRÊN GITHUB (PRIVATE REPOSITORY)
1. Truy cập [github.com](https://github.com) và đăng nhập (hoặc đăng ký miễn phí).
2. Bấm nút **[+]** ở góc trên bên phải → Chọn **New repository**.
3. Điền thông tin:
   - **Repository name:** `bis-ai-project` (hoặc tên tùy thích).
   - Chọn chế độ: **🔒 Private** (Để bảo mật toàn bộ mã nguồn của BIS Textile).
4. Bấm **Create repository**.

---

### BƯỚC 2: TẢI TOÀN BỘ CODE LÊN GITHUB
*(File `.gitignore` đã được cấu hình tự động loại bỏ các file nhạy cảm nên hoàn toàn yên tâm)*

Bạn có thể tải code lên bằng 1 trong 2 cách:
- **Cách đơn giản bằng trình duyệt:** Tại trang repo vừa tạo trên GitHub, bấm nút **"uploading an existing file"** → Kéo toàn bộ các file trong thư mục `G:\My Drive\BIS_AI_PROJECT` thả vào (Lưu ý: Không cần tải `service_account.json` vì đã có cấu hình Secrets ở Bước 4).
- **Hoặc bằng Git command line (nếu máy có git):**
  ```bash
  cd "G:\My Drive\BIS_AI_PROJECT"
  git init
  git add .
  git commit -m "Deploy BIS AI Multi-Agent to Streamlit Cloud"
  git branch -M main
  git remote add origin https://github.com/<TEN_GITHUB_CUA_BAN>/bis-ai-project.git
  git push -u origin main
  ```

---

### BƯỚC 3: KẾT NỐI VÀ DEPLOY TRÊN STREAMLIT CLOUD
1. Truy cập trang chủ: **[share.streamlit.io](https://share.streamlit.io)**
2. Đăng nhập bằng tài khoản **GitHub** của bạn.
3. Bấm nút **"Create app"** (hoặc "New app").
4. Điền các trường thông tin:
   - **Repository:** Chọn repo của bạn (ví dụ `your-name/bis-ai-project`)
   - **Branch:** `main`
   - **Main file path:** `app_ui.py`
   - **App URL (tùy chọn):** Bạn có thể tự đặt tên link, ví dụ `bis-textile` ➔ URL sẽ là `https://bis-textile.streamlit.app`

---

### BƯỚC 4: DÁN CẤU HÌNH BẢO MẬT (SECRETS) ĐỂ KẾT NỐI GOOGLE SHEETS & AI
1. Trước khi bấm Deploy (hoặc sau khi tạo xong, vào mục **Settings > Secrets** của app).
2. Mở file **`STREAMLIT_SECRETS_TEMPLATE.toml`** trong thư mục dự án này.
3. Copy **toàn bộ nội dung** trong file đó và dán vào ô **Secrets** trên giao diện Streamlit Cloud.
4. Bấm **Save** (Lưu).

---

### BƯỚC 5: HOÀN TẤT & TRUY CẬP 24/7
- Streamlit Cloud sẽ tự động cài đặt các thư viện trong `requirements.txt` và khởi động ứng dụng trong khoảng 1 - 2 phút.
- Sau khi khởi động xong:
  - Bạn nhận được một đường link web chính thức (ví dụ: `https://bis-textile.streamlit.app`).
  - **Tắt máy tính, gập laptop, hay mất mạng tại văn phòng thì hệ thống vẫn chạy 24/7 trên Cloud.**
  - Nhập mã PIN nội bộ: **`bis2026`** để mở khóa làm việc.

