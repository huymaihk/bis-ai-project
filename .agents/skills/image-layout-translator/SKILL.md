---
name: image-layout-translator
description: Nhận diện chữ tiếng Anh trên ảnh hoặc tài liệu scan, dịch sang tiếng Việt kỹ thuật dệt may và vẽ đè giữ nguyên vị trí, bố cục ban đầu.
---

### Khi nào kích hoạt:
Khi người dùng yêu cầu:
- Dịch một bức ảnh chứa chữ tiếng Anh sang tiếng Việt.
- Dịch file sơ đồ, catalogue hoặc bảng thông số kỹ thuật dạng ảnh/PDF scan mà không muốn làm vỡ khung.

### Quy trình thực thi của Agent:
1. Kiểm tra file đầu vào của người dùng trong thư mục làm việc.
2. Thực thi lệnh terminal:
   `python .agents/skills/image-layout-translator/run_translator.py "<input_path>" "<output_path>"`
3. Đọc kết quả đường dẫn ảnh đã dịch từ đầu ra terminal và thông báo hoàn thành kèm đường dẫn ảnh mới cho người dùng xem trước.
