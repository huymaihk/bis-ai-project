# React bridge — bước tích hợp 1 và 2 (2026-11-04)

Nguồn frontend: bản xuất AI Studio trong `G:/My Drive/AI/bis-textile-ai-—-hệ-thống-điều-hành-&-chuẩn-hóa-sản-phẩm-dệt-may`.
Bản gốc được giữ nguyên. Bản tích hợp nằm trong `frontend/` của dự án BIS.

## Đã nối
- API Python FastAPI, đăng nhập dùng cấu hình BIS_ACCESS_PIN hiện có, session cookie HttpOnly,
  giới hạn thử PIN, chặn yêu cầu ghi thiếu header/khác origin.
- Đọc cache và bản nháp sản phẩm thật. Sửa theo revision; từ chối bản sửa cũ,
  lưu vào product_drafts, ghi memory version và hủy phê duyệt nội dung khi sửa.
- Danh mục PDF/ảnh giới hạn trong các thư mục nghiệp vụ; đọc trang PDF, xem và tải file gốc sau đăng nhập.
- Bộ nhớ: đọc, tra cứu, ghi chú user, sửa/thu hồi có kiểm tra phiên bản, xem lịch sử.
- Hiển thị nhật ký JobRunner đã có; nút đồng bộ trả trạng thái thực tế từ sync_configured.
- Giao diện thật mặc định; nút riêng mở bản mẫu 3D với nhãn mô phỏng nổi bật.

## Kiểm tra đã thực hiện
- 61 kiểm thử Python đạt (8 API mới + 53 kiểm thử trước).
- TypeScript lint và Vite production build đạt trên ổ C.
- Sửa lỗi nguồn AI Studio: istalking/isTalking không khớp và tên callback của canvas 3D không khớp props.
- Sửa xung đột esbuild/Vite; package-lock cố định dependency tree.
- HTTP trên bản chạy local: trang chủ 200; API chưa đăng nhập 401; đăng nhập 200;
  đọc được 97 sản phẩm và 476 file ảnh/PDF. Không ghi sản phẩm thật trong smoke check.
- Chưa kiểm tra trực quan trong browser. Không suy ra giao diện đã được nghiệm thu từ AppTest/build.

## Cách chạy
Xem frontend/README.md. Build frontend ở checkout ổ C rồi sao chép frontend/dist sang
workspace G nếu chạy Python từ G. `python bis_api.py` mở listener 127.0.0.1:8765.
Không cần đưa khóa Gemini vào frontend. Không thay PIN.

## Công việc tiếp theo
- Nối upload/extraction, chọn ảnh đúng trang/SKU, tìm web, render và duyệt ảnh.
- Nối kiểm tra nội dung/SEO và cổng xuất bản safe_publish; hiện nút Haravan ở chế độ thật bị khóa.
- Nối 17 vai trò agent với queue/worker và sự kiện thật. Văn phòng 3D vẫn là demo 7 nhân vật.
- Cấp hosting API/React với ổ lưu bền vững, HTTPS, quản lý session và điều phối ghi nhiều tiến trình trước khi public.
- Streamlit Cloud hiện không tự chạy API này khi push code; website cũ chưa được thay bằng React.
- Google sync chưa được khắc phục; dữ liệu local vẫn là bản lưu chính trong phiên này.

Không có thao tác tạo, sửa hoặc xóa sản phẩm Haravan trong đợt tích hợp.
