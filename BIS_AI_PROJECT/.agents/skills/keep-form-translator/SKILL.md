---
name: keep-form-translator
description: Dịch file PDF, DOCX, XLSX, HTML từ tiếng Anh sang tiếng Việt giữ nguyên 100% định dạng, bảng biểu, ảnh, font chữ và style bằng PDFMathTranslate (pdf2zh), Deep-Translator và bộ từ điển chuyên ngành TEXTILE_GLOSSARY.
---

# KỸ NĂNG DỊCH TÀI LIỆU GIỮ NGUYÊN 100% FORMAT (KEEP-FORM TRANSLATOR)

Kỹ năng này chuyên biệt xử lý dịch tài liệu kỹ thuật, tiêu chuẩn dệt may (AATCC, ISO, ASTM), hướng dẫn sử dụng (Manuals), bảng thông số (Datasheets) và báo cáo kiểm định từ tiếng Anh sang tiếng Việt với tiêu chí:
**BẢO TOÀN 100% CẤU TRÚC, ĐỊNH DẠNG, BẢNG BIỂU, FONT, MÀU SẮC, HÌNH ẢNH VÀ CÔNG THỨC.**

---

## 1. NGUYÊN TẮC BẮT BUỘC ÁP DỤNG TỪ ĐIỂN DỆT MAY (`TEXTILE_GLOSSARY`)
Mọi tác vụ dịch tài liệu bắt buộc phải nạp và ưu tiên tra cứu bộ từ điển `TEXTILE_GLOSSARY` trong `keep_form_translator.py` trước khi gọi dịch máy:
- **Color Fastness** ➔ Độ bền màu
- **Dimensional Stability** ➔ Độ ổn định kích thước (độ co rút)
- **Tensile Strength** ➔ Độ bền kéo đứt
- **Tear Strength** ➔ Độ bền xé rách
- **Bursting Strength** ➔ Độ bền bục
- **Pilling Resistance** ➔ Khả năng chống xù lông / vón gút
- **Abrasion Resistance** ➔ Khả năng chống mài mòn
- **Yarn Count** ➔ Chỉ số sợi
- **Fabric Density / Thread Density** ➔ Mật độ dệt / Mật độ sợi
- **Water Repellency / Resistance** ➔ Khả năng kháng nước / chống thấm
- **Moisture Management** ➔ Quản lý độ ẩm / thấm hút mồ hôi
- **Washing Fastness** ➔ Độ bền màu giặt
- **Rubbing Fastness / Crocking** ➔ Độ bền màu ma sát (Crockmeter)
- **Perspiration Fastness** ➔ Độ bền màu mồ hôi
- **Light Fastness** ➔ Độ bền màu ánh sáng
- **AATCC** ➔ Hiệp hội các nhà Hóa học và Màu Dệt Dệt may Hoa Kỳ
- **ISO** ➔ Tổ chức Tiêu chuẩn hóa Quốc tế
- **ASTM** ➔ Hiệp hội Thử nghiệm và Vật liệu Hoa Kỳ

---

## 2. QUY TRÌNH XỬ LÝ THEO TỪNG ĐỊNH DẠNG FILE

### A. File Word (.docx): Can thiệp Run Text Level
- **Không bao giờ** đọc toàn bộ tài liệu thành text thô rồi xuất lại.
- Dùng thư viện `python-docx` duyệt qua từng đối tượng `doc.paragraphs` và `doc.tables`.
- **Can thiệp trực tiếp ở cấp độ `run.text`**:
  - Giữ nguyên toàn bộ thuộc tính style của Run: `run.font.name`, `run.font.size`, `run.bold`, `run.italic`, `run.underline`, `run.font.color.rgb`.
  - Giữ nguyên cấu trúc thụt đầu dòng (indentation), khoảng cách dòng (line spacing) và bullet points.
- Với các bảng biểu (`table.rows` ➔ `cell.paragraphs`): dịch nội dung từng ô, bảo toàn độ rộng cột (`cell.width`), viền bảng (border) và màu nền ô (shading).

### B. File Excel (.xlsx): Can thiệp Cell Value Level
- Mở file bằng `openpyxl.load_workbook(file_path, data_only=False)` để bảo vệ công thức tính.
- Duyệt qua từng ô `cell` trên tất cả các Sheet:
  - **Bỏ qua 100% công thức**: Nếu `cell.value` bắt đầu bằng dấu `=`, tuyệt đối không chạm vào.
  - Chỉ dịch các chuỗi văn bản (`isinstance(cell.value, str)`).
  - Giữ nguyên vẹn 100% định dạng ô: font, size, fill color, borders, alignment, number_format, row_height và column_dimensions.

### C. File HTML (.html / .htm): Can thiệp DOM Text Nodes
- Phân tích cú pháp bằng `BeautifulSoup(html_content, 'html.parser')`.
- Chỉ tìm và thay thế các node văn bản `NavigableString`.
- Bảo toàn tuyệt đối 100% các thẻ cấu trúc (`<div>`, `<span>`, `<table>`, `<tr>`, `<td>`, `<img>`, `<svg>`), các class CSS, inline `style="..."`, thuộc tính bố cục CSS Flexbox, Grid và responsive layout.

### D. File PDF (.pdf): Tích hợp `pdf2zh` & `keep_form_translator.py`
1. **Qua MCP Server `pdf-translator` hoặc CLI `pdf2zh`**:
   - Sử dụng mô hình `DocLayout-YOLO` để phân đoạn trang thành các khối: Text, Header, Table, Formula, Figure.
   - Lệnh thực thi:
     ```bash
     pdf2zh <input_path> -li en -lo vi -s google
     ```
   - Xuất ra 2 bản: Bản dịch tiếng Việt (`_mono.pdf`) và Bản song ngữ đối chiếu (`_dual.pdf`).
2. **Qua engine nội tại `keep_form_translator.py`**:
   - Dùng `pymupdf` (PyMuPDF) trích xuất từng text block kèm font, kích thước, tọa độ `bbox = (x0, y0, x1, y1)`.
   - Sử dụng hàm vẽ đè / inpainting text lên nền gốc, bảo toàn các ảnh vector và biểu đồ kỹ thuật.

---

## 3. LỆNH MẪU KÍCH HOẠT NHANH
Khi người dùng yêu cầu dịch tài liệu giữ format:
```bash
python keep_form_translator.py --input "tailieu.docx" --output "tailieu_vi.docx"
python keep_form_translator.py --input "bang_thong_so.xlsx" --output "bang_thong_so_vi.xlsx"
pdf2zh "datasheet.pdf" -li en -lo vi -s google
```
