# BẢNG BÀN GIAO TIẾN ĐỘ & NGỮ CẢNH DỰ ÁN (PROJECT HANDOVER)
*Hệ thống Multi-Agent AI BIS Textile - Tự động đồng bộ giữa các máy tính*

---

## 1. Thông tin chung
* **Dự án**: BIS_AI_PROJECT (BIS Textile Multi-Agent System & Pipeline)
* **Thời điểm cập nhật**: 2026-11-03
* **Vị trí lưu trữ chia sẻ**: `G:\My Drive\BIS_AI_PROJECT` (Google Drive)
* **GitHub Repository**: `huymaihk/bis-ai-project` (Nhánh: `main`)
* **Deploy Cloud**: Streamlit Cloud (`https://bisaitextile.streamlit.app`)
* **Database Quản lý**: Google Sheets `BIS_Textile_Product_Master`
* **Sàn TMĐT mục tiêu**: Haravan (Shop: `BIS TEXTILE N8N PRODUCT SYNC`, Guard Rail: `HARAVAN_PUSH_ENABLED = False`)

---

## 2. Kiến trúc & Nhân sự AI (Multi-Agent Team)
1. **Leader (`agent_leader.py`)**: Điều phối tổng thể toàn bộ pipeline.
2. **Technical Agent (`agent_technical.py`)**: Đọc hiểu và chuẩn hóa thông số vải (GSM, Width, Thành phần sợi, Kiểu dệt, Hoàn tất).
3. **Media Agent (`agent_media.py`)**: Tạo ảnh studio, xử lý background, composite ảnh vải (Imagen 3 / Pollinations).
4. **Translator Agent (`agent_translator.py` & `keep_form_translator.py`)**: Dịch tài liệu giữ nguyên 100% định dạng, thuật ngữ chuyên ngành dệt may.
5. **Marketing Agent (`agent_marketing.py`)**: Sinh nội dung bán hàng, mô tả sản phẩm chuẩn SEO.
6. **Knowledge Agent (`agent_knowledge.py`) & Learning Engine (`learning_engine.py`)**: Quản lý tri thức và học từ feedback.
7. **Haravan Uploader (`haravan_uploader.py`)**: Đẩy sản phẩm lên Haravan có rào chắn bảo vệ.
8. **App UI (`app_ui.py`)**: Giao diện Streamlit tương tác tích hợp phòng làm việc 3D (`bis_textile_3d_office.html`, `lego_hq.html`).

---

## 3. Trạng thái công việc hiện tại (Current Status)
* [x] Bộ nhớ bền vững: lịch sử, hiệu chỉnh phiên bản, thu hồi, truy xuất ngữ cảnh; xem MEMORY_GUIDE.md.
* [x] Chat Gemini được nối vào lịch sử đã lưu; vô hiệu tiến độ ngẫu nhiên và phản hồi tool giả trong chat.
* [ ] Đồng bộ tự động đã được chủ dự án duyệt và cấu hình đúng bảng BIS; hiện bị chặn bởi khóa service account local lỗi invalid_grant / Invalid JWT Signature. Cần thay khóa hợp lệ trong cấu hình bảo mật.
* [ ] Chưa kiểm thử đầy đủ pipeline Haravan/Google Sheets/Gemini thực tế trong đợt nâng cấp bộ nhớ.
* Lưu ý: các trạng thái “ổn định” ở bàn giao cũ dưới đây là thông tin lịch sử, không phải kết quả kiểm thử của đợt này.

* [x] Đã cấu hình và kiểm tra hệ sinh thái Multi-Agent hoạt động ổn định.
* [x] Đã tích hợp các custom skill trong `.agents/skills/`:
  - `keep-form-translator`: Dịch giữ format PDF/Word/Excel.
  - `image-layout-translator`: Dịch và vẽ đè chữ trên ảnh kỹ thuật.
* [x] Đã thiết lập cơ chế tự động đồng bộ ngữ cảnh làm việc (Conversation & Brain) giữa 2 máy.
* [ ] Kiểm tra kết nối Haravan Token và Google Service Account trên máy thứ hai.
* [ ] Rà soát dữ liệu sản phẩm trong `extracted_products_cache.json` và bảng tính Google Sheets.

---

## 4. Hướng dẫn dành cho Antigravity khi mở trên máy mới
1. Đọc kỹ file này (`PROJECT_HANDOVER.md`) và file cấu hình `config.py`.
2. Kiểm tra các biến môi trường hoặc file `.env` / `STREAMLIT_SECRETS_TEMPLATE.toml`.
3. Báo cáo ngắn gọn cho người dùng: *"Tôi đã nạp đầy đủ bối cảnh từ máy trước, sẵn sàng tiếp tục công việc!"*


## Xác minh đợt nâng cấp
- 9 kiểm thử unit và kiểm tra giao diện thêm/sửa/khởi động phiên mới: đạt.
- Bản sao Google Sheets qua kết nối Google Drive: 32 sự kiện đã đọc lại khớp toàn bộ; không sửa tab sản phẩm.
- Đồng bộ tự động Python local: chưa chạy được vì Invalid JWT Signature của service account hiện có.
- Kiểm tra Gemini thật: API trả 503 UNAVAILABLE do model quá tải; không phải bằng chứng sai API key. Chat lưu yêu cầu trước khi gọi AI và thông báo lỗi rõ khi chưa có phản hồi.
- Bản code đã chuẩn bị ở ổ G và bản Git local. Chủ dự án đã duyệt commit/push lên main để triển khai Streamlit. Kiểm tra trạng thái deploy thực tế trước khi tuyên bố tất cả chức năng online đã chạy.
