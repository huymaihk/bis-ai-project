---
name: keep-form-translator
description: Dịch file PDF, DOCX, XLSX, HTML từ tiếng Anh sang tiếng Việt giữ nguyên 100% định dạng, bảng biểu, ảnh và style bằng PDFMathTranslate (pdf2zh) và Deep-Translator.
---

# KỸ NĂNG DỊCH TÀI LIỆU GIỮ NGUYÊN 100% FORMAT (KEEP-FORM TRANSLATOR)

Kỹ năng này chuyên biệt xử lý dịch tài liệu kỹ thuật, tiêu chuẩn dệt may (AATCC, ISO, ASTM), hướng dẫn sử dụng (Manuals), bảng thông số (Datasheets) và báo cáo kiểm định từ tiếng Anh sang tiếng Việt với tiêu chí:
**BẢO TOÀN 100% CẤU TRÚC, ĐỊNH DẠNG, BẢNG BIỂU, FONT, MÀU SẮC, HÌNH ẢNH VÀ CÔNG THỨC.**

## QUY TẮC THỰC THI CHO TỪNG ĐỊNH DẠNG:

### 1. File PDF (Datasheet, Catalog, Tiêu chuẩn kỹ thuật):
- Sử dụng công cụ `pdf2zh` (PDFMathTranslate) bóc tách tài liệu qua mô hình `DocLayout-YOLO`.
- Lệnh thực thi:
  `pdf2zh <file_path> -li en -lo vi -s google`
  (hoặc qua MCP Server `pdf-translator`).
- Kết quả tạo ra file PDF tiếng Việt và file PDF song ngữ (Dual-language) giữ nguyên vẹn 100% vector layout, hình ảnh, bảng biểu và công thức toán học/hóa học.

### 2. File Word (.docx):
- KHÔNG đọc toàn bộ file ra Markdown rồi tạo lại file mới.
- Sử dụng `python-docx` duyệt qua từng cấu trúc XML gốc:
  - Duyệt qua `doc.paragraphs` và `doc.tables`.
  - Can thiệp ở cấp độ `run.text` (giữ nguyên font chữ, in đậm, in nghiêng, màu sắc RGB, bullet points).
  - Duyệt qua từng ô `cell.paragraphs` trong bảng biểu để giữ nguyên độ rộng cột và viền bảng.
- Gọi `deep_translator.GoogleTranslator(source='en', target='vi')` hoặc thuật ngữ dệt may chuyên ngành chuẩn BIS Textile.

### 3. File Excel (.xlsx):
- Sử dụng `openpyxl` mở workbook với `data_only=False` để bảo vệ công thức.
- Duyệt qua từng ô `cell.value` trong tất cả các Sheet:
  - BỎ QUA các ô chứa công thức toán học (bắt đầu bằng dấu `=`).
  - Chỉ dịch các chuỗi văn bản (string) tiêu đề cột, chú giải, mô tả thông số.
  - Giữ nguyên 100% định dạng cell: font, fill color, border, alignment, number_format.

### 4. File HTML (.html / .htm):
- Sử dụng `BeautifulSoup(html_content, 'html.parser')`.
- Chỉ tìm và dịch các node `NavigableString` (văn bản hiển thị).
- Giữ nguyên 100% các thẻ HTML (`<table>`, `<tr>`, `<td>`, `<div>`, `<span>`, `<img>`), các thuộc tính `class`, `style`, CSS Grid và Flexbox.

### 5. Thuật ngữ dệt may chuyên ngành chuẩn hóa (Glossary):
- GSM: Định lượng vải (g/m²)
- Yarn Count: Chỉ số sợi (Ne, Nm, Dtex)
- Color Fastness: Độ bền màu
- Dimensional Stability: Độ ổn định kích thước / Độ co rút
- Tensile Strength: Độ bền kéo đứt
- Tear Strength: Độ bền xé rách
- Pilling Resistance: Khả năng chống xù lông / vón gút
- AATCC: Hiệp hội các nhà Hóa học và Màu Dệt Dệt may Hoa Kỳ
- ISO: Tổ chức Tiêu chuẩn hóa Quốc tế

