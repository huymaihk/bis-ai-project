# 🎯 BỘ PROMPT & HƯỚNG DẪN RA LỆNH CHO AI ĐỂ TỐI ƯU GIAO DIỆN STREAMLIT (BIS TEXTILE AI)

---

## 📌 1. LINK CODE GIAO DIỆN FULL (DÙNG ĐỂ GỬI CHO AI)

- **Link file trên máy local:** [app_ui.py](file:///G:/My%20Drive/BIS_AI_PROJECT/app_ui.py)
- **Link GitHub xem trực tiếp:** [GitHub BIS_AI_PROJECT/app_ui.py](https://github.com/huymaihk/bis-ai-project/blob/main/BIS_AI_PROJECT/app_ui.py)
- **Link RAW (AI có thể đọc trực tiếp bằng URL):** `https://raw.githubusercontent.com/huymaihk/bis-ai-project/main/BIS_AI_PROJECT/app_ui.py`

---

## 🚀 2. CÂU LỆNH MẪU (PROMPT) ĐỂ RA LỆNH CHO AI TỐI ƯU & NÂNG CẤP GIAO DIỆN

*(Copy toàn bộ đoạn khung dưới đây và dán vào AI của bạn)*

```markdown
Chào bạn, tôi là Product Owner của hệ thống "BIS Textile Multi-Agent E-commerce Platform" (Hệ thống AI tự động hóa trích xuất Catalogue thiết bị thí nghiệm dệt may, chuẩn hóa dữ liệu SEO kỹ thuật và đẩy bán hàng lên Haravan/Google Sheets).

Dưới đây là toàn bộ mã nguồn file giao diện chính `app_ui.py` (viết bằng Python Streamlit, khoảng 2.100 dòng code):
[DÁN CODE APP_UI.PY HOẶC ĐÍNH KÈM FILE TẠI ĐÂY - HOẶC ĐƯA LINK RAW: https://raw.githubusercontent.com/huymaihk/bis-ai-project/main/BIS_AI_PROJECT/app_ui.py]

---

### 🎯 MỤC TIÊU CỦA BẠN:
Đóng vai trò là một **Senior Fullstack UI/UX Designer & Streamlit Expert**, bạn hãy phân tích toàn diện, tái cấu trúc và nâng cấp giao diện này lên cấp độ chuyên nghiệp, hiện đại, mượt mà và tối ưu hiệu năng cao nhất.

---

### 📋 CẤU TRÚC HỆ THỐNG GIAO DIỆN HIỆN TẠI (7 TABS):
1. **Header & Thanh điều khiển:** Đăng nhập bảo mật, Đồng bộ Google Drive, Reset hệ thống, Trạng thái Haravan Guard.
2. **Tab 1: Văn phòng 3D Lego AI Team:** Mô phỏng phòng điều hành Multi-Agent (Leader, Technical, Marketing, Media, Knowledge, Operations).
3. **Tab 2: Phê duyệt Sản phẩm & Live Preview:** Bảng đối soát trùng/không trùng, Bộ lọc SKU, Trình soạn thảo 7 khối nội dung Haravan và Live Preview HTML Responsive.
4. **Tab 3: Nghiên cứu SEO & Marketing (Agent_Marketing):** Tự động cào và học hỏi phong cách từ 4 website ngành (bistextile, qclabtex, labgartex, bisvn), sinh Meta Title, Meta Description, URL Slug, Schema JSON-LD.
5. **Tab 4: Studio Ảnh & Duyệt Ảnh Mockup (Agent_Media):** Tìm kiếm ảnh web đa nguồn (Bing Engine), xem trước nhiều ảnh (Live Gallery), trích xuất thông minh từ PDF (Multi-page scan), phối cảnh nền Mockup phòng Lab dệt may.
6. **Tab 5: Kho Lưu Trữ Tri Thức (Agent_Knowledge):** Quản lý Sách tiêu chuẩn AATCC/ISO, Manual, CO/CQ, tài liệu kỹ thuật liên kết Google Drive.
7. **Tab 6: Phân Hệ Vận Hành & Haravan Guard (Agent_Operations):** Đối soát trùng lặp 2 chiều (website bistextile.com & Google Sheets), đẩy sản phẩm ẩn an toàn, khóa mốc lịch sử 20/10.
8. **Tab 7: Bộ Nhớ Tự Học (Learning Engine):** Quản lý Few-shot rules, ghi nhớ các phản hồi/chỉnh sửa của người dùng để cải thiện chất lượng bóc tách.

---

### 🛠️ CÁC YÊU CẦU TỐI ƯU & NÂNG CẤP CẦN THỰC HIỆN:

1. **Nâng cấp Thẩm mỹ & Visual UI/UX:**
   - Áp dụng triệt để phong cách **Dark Modern Glassmorphism** (nền tối sang trọng `#0b0f19`, hiệu ứng mờ kính `backdrop-filter: blur()`, viền neon mỏng tinh tế `#38bdf8`, `#10b981`, `#818cf8`).
   - Tối ưu Typography, khoảng cách padding/margin, bố cục lưới (Grid) responsive chuẩn trên cả Laptop, Desktop màn hình rộng và Tablet.
   - Thêm các Micro-animations (hiệu ứng hover card nhẹ nhàng, badge trạng thái nhấp nháy êm ái).

2. **Tối ưu Hiệu năng & Trải nghiệm Người dùng (Performance & UX):**
   - Loại bỏ giật lag khi chuyển Tab hoặc khi lưu chỉnh sửa sản phẩm.
   - Tối ưu hóa `@st.cache_data` và `@st.cache_resource` để tránh re-render không cần thiết.
   - Cải tiến Live Preview HTML: Đảm bảo bản xem trước hiển thị tức thì, mượt mà mà không làm mất focus của ô nhập liệu.

3. **Cải tiến Tính năng Thao tác Nhanh (Productivity):**
   - Thêm nút phím tắt hoặc thanh công cụ cố định (Sticky Toolbar) khi cuộn trang kiểm duyệt.
   - Hiển thị thanh tiến độ (Progress bar) khi quét ảnh hoặc phân tích AI.
   - Tối ưu hóa bộ lọc sản phẩm: tìm kiếm nhanh theo SKU hoặc từ khóa bằng search bar tức thì.

4. **Yêu cầu Kỹ thuật:**
   - Giữ nguyên toàn bộ logic nghiệp vụ cốt lõi (Haravan Guard 20/10, cơ chế Singleton Multi-Agent, tích hợp Google Sheets & Drive).
   - Đảm bảo mã nguồn sạch sẽ (Clean Code), có chú thích rõ ràng, tương thích 100% với phiên bản Streamlit 1.35+.

---

Hãy cung cấp:
1. **Bản phân tích đánh giá** các điểm cần cải thiện của code hiện tại.
2. **Toàn bộ mã nguồn `app_ui.py` đã được tối ưu hoàn chỉnh** (viết đầy đủ, không cắt xén).
```
