# Đánh giá và hướng nâng cấp BIS — 2026-11-04

Đánh giá người dùng: Technical/Marketing khoảng 50%, đăng ảnh/chống trùng khoảng 80%; các phòng còn lại chưa đạt. Đây là đánh giá nghiệm thu của người dùng, không phải số đo tự động.

## Phát hiện đã kiểm tra
- agent_media.extract_image_from_pdf chọn ảnh đầu danh sách sắp theo dung lượng trên trang; không xác minh ảnh khớp SKU. Catalogue mẫu: SKU 03026A xuất hiện trang 7 với 4 image resources, chưa phải 4 ảnh sản phẩm đã xác minh.
- fetch_brand_image_from_web nhận ảnh tải thành công đầu tiên; thiếu xác minh danh tính từ SKU + tên tiếng Anh + ảnh tham chiếu PDF.
- is_duplicate_product: kiểm tra substring trong tên variant và mọi token tiếng Anh xuất hiện trong body; nguy cơ trùng giả. Cần kết quả MATCH/REVIEW/NO_MATCH thay vì gộp tất cả thành trùng chắc chắn.
- Marketing fallback khi API lỗi vẫn sinh cam kết chính hãng/CO-CQ; cần đánh dấu lỗi và giữ dữ liệu thiếu chứng cứ, không tạo cam kết tự động.
- Đã xem trực tiếp AATCC Weight Trio on BIS Backdrop.png: chuẩn cảm nhận gồm chữ dập, vật liệu, ánh sáng, bóng tiếp xúc. Chưa đánh giá toàn bộ ảnh mẫu hoặc chứng nhận mọi ảnh đúng sản phẩm.

## Nguồn GitHub đã tra cứu
- https://github.com/langchain-ai/langgraph : điều phối trạng thái, checkpoint, chờ duyệt, tiếp tục tác vụ.
- https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart : tham khảo kết hợp Gemini và LangGraph; không coi web research là xác minh ảnh sản phẩm.
- https://github.com/confident-ai/deepeval : đánh giá đầu ra AI; không thay thế assert quy tắc nghiệp vụ và nghiệm thu con người.
- https://github.com/pymupdf/PyMuPDF : trích ảnh và vị trí, render trang để chọn vùng; kiểm tra giấy phép trước khi phân phối tích hợp.
- https://github.com/microsoft/playwright : kiểm thử luồng giao diện và hồi quy.
Chưa cài hoặc tích hợp framework mới. Cần đánh giá phiên bản, giấy phép và phụ thuộc trước khi triển khai.

## Kiến trúc đề xuất
Nguồn -> trích dữ kiện/chứng cứ -> chọn ảnh ứng viên -> kiểm tra kỹ thuật -> nội dung theo template -> kiểm tra ảnh -> người dùng duyệt -> xuất bản nháp -> xác minh -> ghi bộ nhớ.
Mỗi bước có job ID, input/output, phiên bản, lỗi, retry hữu hạn và trạng thái chờ duyệt. UI chỉ hiển thị trạng thái thật.

## Thứ tự và tiêu chí nghiệm thu
1. Media nguồn: liệt kê ảnh trên trang chứa SKU, ảnh xem trước toàn trang, tọa độ và độ phân giải; chọn/tải từng ảnh hoặc ZIP. Scan/vector phải có render/crop, không tự gọi trang nguyên vẹn là ảnh sản phẩm.
2. Tìm web: truy vấn SKU + tên Anh + hãng; nguồn trang, ảnh gốc, đối chiếu thị giác với PDF; không đủ chứng cứ thì NEEDS_REVIEW. Không dùng ảnh đầu tiên như kết quả xác minh.
3. Technical/Marketing: dựng HTML từ dữ liệu có schema; kiểm tra mã SKU, 7 khối có ngoại lệ bảng ít thông số, thông tin cấm, meta 140–160 ký tự. Không bịa thông số/CO-CQ.
4. Media thành phẩm: giữ ảnh mẫu nguyên vẹn; so sánh trước/sau cùng SKU; kiểm tra chữ/logo/hình khối; người dùng duyệt độ chân thật. Không dùng tăng kích thước thay cho độ chi tiết nguồn.
5. Operations: kiểm thử biến thể SKU gần nhau, nhắc SKU trong phụ kiện, nội dung chung, dữ liệu thiếu, chạy lại, timeout sau POST; đối soát ID/hash và draft trước upload.
6. UI: 5 bước Nhập nguồn / Nội dung / Ảnh / Duyệt & xuất / Bộ nhớ & lịch sử; chuyển văn phòng 3D sang mục phụ. Quyết định layout cuối cần thử trên dữ liệu thực.
7. Tự học: đề xuất quy tắc từ hiệu chỉnh, kiểm tra bộ hồi quy rồi mới kích hoạt; quy tắc mới không ghi đè sự thật nguồn. Tự fix trong nhánh riêng, giới hạn số vòng, test độc lập không cho tự nới để đạt.

## Trạng thái
Đây là nghiên cứu và kiểm tra mã sơ bộ, chưa hoàn tất nâng cấp các phòng ban. Chưa chạy nghiệm thu E2E, chưa sửa/deploy code nghiệp vụ trong lượt này. Bộ nhớ tự đồng bộ vẫn cần xác minh credential. Không sử dụng 9 test bộ nhớ trước đây làm bằng chứng chất lượng toàn hệ thống.
