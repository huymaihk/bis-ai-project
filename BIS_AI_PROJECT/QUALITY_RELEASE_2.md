# BIS Quality Release 2 — 2026-11-04

## Thay đổi đã triển khai trong mã
- Giao diện mặc định 5 bước; UI phòng ban/3D cũ nằm sau tùy chọn nâng cao.
- Nội dung 7 khối dựng bằng template thoát HTML, chỉ lấy thông số đã nhập; thiếu chứng cứ/không khớp trích dẫn bị chặn duyệt/đăng.
- Bản SEO có đếm ký tự và giữ SKU/tên gốc; xung đột giữa tên dài với giới hạn 140–160 cần biên tập, không tự cắt mất định danh. Chưa xác minh ánh xạ SEO vào theme Haravan.
- PDF chọn đúng trang chứa SKU, giữ ảnh gốc và soft mask, ZIP có provenance; có xem toàn trang/cắt vùng cho PDF scan/vector. Chưa có OCR tự động nhận SKU trong scan.
- Ảnh web giữ tên truy vấn đầy đủ, metadata trang nguồn và xếp hạng ứng viên; người dùng đối chiếu. Không gọi ảnh đầu tiên là đã xác minh. Google Search cần GOOGLE_SEARCH_API_KEY và GOOGLE_SEARCH_CX; không cấu hình thì dùng DDGS khi dịch vụ khả dụng.
- Ghép ảnh studio 1254x1254 từ nguồn đủ lớn, không phóng thumbnail và không tự tăng sắc nét/màu toàn ảnh. Có tùy chọn tách nền trắng; vật thể trắng có thể bị mất viền, phải kiểm tra.
- Chỉnh ảnh Gemini dùng ảnh sản phẩm + nền tham chiếu, không dựng thiết bị từ tên. Dùng SDK google-genai>=2.33.0 và model BIS_IMAGE_MODEL (mặc định gemini-nano-banana-2.1 theo docs). Lỗi model/quota hiển thị rõ. Chất lượng đầu ra API thật chưa nghiệm thu trong release này.
- Nhập ảnh thành phẩm luôn PENDING_REVIEW; duyệt gắn SHA256. Sửa file sau duyệt chặn đăng. Không xóa/ghi đè ảnh mẫu hoặc ảnh đã duyệt; từ chối chỉ đổi trạng thái.
- Đối soát MATCH/REVIEW/NO_MATCH, kiểm tra SKU đầy đủ; nhắc mã trong nội dung/phụ kiện/mã số gốc là REVIEW. Legacy caller vẫn khóa cả REVIEW để tránh đăng nhầm.
- Mọi đường tạo sản phẩm dùng safe_publish: cờ bật đăng + trạng thái duyệt + hash nội dung + nguồn + SEO + ảnh duyệt + checkpoint đồng bộ + quét live toàn bộ + tạo nháp ẩn + đọc lại ID/SKU/trạng thái/ảnh.
- Có khóa liên tiến trình, nhật ký trước POST. Timeout hoặc kết quả không khớp -> RECONCILE_REQUIRED, không tự POST lại.
- Không có lệnh xóa hoặc cập nhật sản phẩm trong cổng đăng mới. Không tự bật HARAVAN_PUSH_ENABLED.
- Quét live thất bại không ghi đè snapshot và không báo thành công. Không clear toàn bộ Sheet để dọn trùng.
- Tri thức: sửa lỗi register_document, đánh dấu metadata chưa thẩm định; index PDF theo trang/hash, cập nhật tài liệu sẽ thu hồi chunk cũ. Scan quá ít chữ được báo cần OCR.
- JobRunner ghi job ID, input/output hash và lỗi thật; có lịch sử tác vụ trong UI. Chưa phải worker nền tự chạy khi Streamlit ngủ.
- Loại bỏ token viết trực tiếp khỏi file ghi chú haravan_publisher.py; chỉ đọc credential qua config.
- Bộ kiểm thử và GitHub Actions được thêm để tự chạy trên push/PR. Tự sửa code trong phiên phát triển dựa vào lỗi test; chưa có agent nền tự sửa và tự deploy không giám sát.

## Kiểm chứng
- Bộ kiểm thử nội dung, PDF, ảnh, đăng giả lập, bộ nhớ và UI: 52 tình huống (chạy kết quả cuối trước triển khai).
- AppTest mở app_ui với dữ liệu local, phiên đã xác thực: 5 tab, không có exception.
- Đã xem contact sheet 9 ảnh mẫu trong 6_Final_Composites, giữ nguyên mọi file benchmark.
- Browser preview local bị cổng quyền trình duyệt từ chối, chưa xác minh trực quan giao diện bằng trình duyệt.
- Haravan tạo/đọc lại được kiểm thử bằng fake API; không tạo, sửa hoặc xóa sản phẩm thật trong release.
- Đồng bộ Python local vẫn lỗi Invalid JWT Signature theo trạng thái trước đó; không tuyên bố đã sửa khóa.

## Vận hành
1. Mở giao diện mới, chọn PDF và trích một trang; không ghi đè bản sản phẩm đã biên tập.
2. Chỉnh dữ liệu và trích dẫn, kiểm tra 7 khối, chỉnh SEO.
3. Chọn ảnh PDF/web/upload; tạo bản studio hoặc chỉnh Gemini hoặc nhập ảnh web đã làm; đối chiếu nguồn và benchmark rồi duyệt.
4. Duyệt phiên bản nội dung. Cổng đăng chỉ tạo bản nháp khi toàn bộ điều kiện đạt.
5. Nếu đăng bị chặn do Google credential: sửa chứng thực bảo mật trước, không xóa ledger/lock để thử POST mù.
6. Phiên cũ có trạng thái APPROVED phải duyệt lại trong UI mới để tạo hash phiên bản.
7. Chạy python -m unittest test_quality_workflow test_persistent_memory test_production_workspace -v.

## Tham khảo
- https://github.com/langchain-ai/langgraph
- https://github.com/confident-ai/deepeval
- https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart
- https://github.com/microsoft/playwright
- https://github.com/pymupdf/PyMuPDF
- https://ai.google.dev/gemini-api/docs/image-generation
- https://docs.haravan.com/docs/omni-apis/products/

Release dùng các cơ chế nhỏ có thể kiểm thử trong kiến trúc hiện có; chưa cài LangGraph/DeepEval/Playwright vào runtime BIS.

