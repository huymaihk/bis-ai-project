# BIS Workspace — giao diện 2026-11-04

## Tham khảo
- Hai video chủ dự án gửi: video 1793676859936 dài 60,47 giây, video 1793772145876 dài 48,23 giây. Xem các khung hình phân bố theo thời gian; đánh giá phần hình ảnh, không phiên âm âm thanh.
- Video 1: nền tối, chữ lớn, điểm nhấn đỏ, khoảng cách rõ giữa các nội dung. Video 2: agent có hình đại diện và mô tả luồng phối hợp. Áp dụng robot bằng CSS và sơ đồ vai trò dạng chữ, chưa dựng văn phòng 3D hay canvas kéo thả.
- https://github.com/langflow-ai/langflow — tham khảo tổ chức workflow.
- https://github.com/open-webui/open-webui — tham khảo không gian làm việc với thanh bên.
- https://github.com/langchain-ai/agent-chat-ui — tham khảo phân tách lịch sử/ngữ cảnh; repository đã được đánh dấu archived khi tra cứu. Không thêm dependency từ các dự án này.

## Thay đổi
- Module workspace_design.py cung cấp bảng màu tối/sáng, phần mở đầu với biểu tượng agent, bốn số liệu từ dữ liệu đã lưu, kiểu form/tab/upload nhất quán và bố cục thu gọn trên màn hình nhỏ.
- Chọn SKU trên thanh bên; nhận diện sản phẩm được nhắc lại trong Nội dung, Ảnh, Duyệt & xuất; tên/SKU được escape trước khi hiển thị HTML.
- Giữ năm tab nghiệp vụ. Trạng thái ảnh/nội dung là trạng thái bản lưu, không phải xác nhận kết nối API hay chất lượng đã nghiệm thu.
- Không chỉnh PIN hoặc cấu hình đăng nhập. Không thực hiện nghiệp vụ Haravan trong lượt này.

## Xác minh và giới hạn
- 53 kiểm thử offline đạt: bộ nhớ, nghiệp vụ với API giả, giao diện AppTest và chuyển sáng/tối vẫn giữ SKU/cổng duyệt.
- Chưa kiểm tra ảnh chụp giao diện trong trình duyệt. Quyền mở preview localhost trước đó bị từ chối; không dùng cách khác để vượt hạn chế đó.
- Streamlit Cloud cần build lại từ commit mới; test không chứng minh bản cloud đã hiển thị đúng.
- Đồng bộ Google tự động vẫn chưa được khắc phục trong đợt giao diện này.
