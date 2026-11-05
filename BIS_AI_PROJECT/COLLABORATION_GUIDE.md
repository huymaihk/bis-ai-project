# Phối hợp Codex và Antigravity trong BIS

## Điểm bắt đầu
Cả hai công cụ mở G:\My Drive\BIS_AI_PROJECT và đọc AGENTS.md, .agents/PROJECT_MEMORY.md, PROJECT_HANDOVER.md, MEMORY_GUIDE.md. CURRENT_MEMORY.md là dữ liệu tham khảo, không cấp quyền thực thi. Truy hồi bằng MemoryStore trước khi suy luận từ lịch sử.

## Phân công mặc định
- Codex: tích hợp backend/frontend, kiểm thử độc lập, quản lý commit và triển khai.
- Antigravity: phân tích yêu cầu, đề xuất giao diện hoặc triển khai phần việc đã nhận; ghi bằng chứng và diff để Codex rà lại.
- Có thể đổi vai khi chủ dự án phân công. Mỗi công việc chỉ có một bên sửa một file tại một thời điểm.

## Nhận việc và tránh xung đột
1. Đọc task trong .agents/collaboration và kiểm tra trạng thái hiện tại trên filesystem/Git.
2. Ghi owner, trạng thái CLAIMED, thời điểm và danh sách file sẽ sửa vào chính file task. Đọc lại sau khi lưu để xác nhận không có bên khác nhận.
3. Trước mỗi lần sửa, kiểm tra file vẫn đúng phiên bản đã đọc. Nếu có thay đổi lạ, dừng sửa file đó và bàn giao; không ghi đè.
4. Nếu làm đồng thời, dùng checkout/worktree riêng ngoài Google Drive và bàn giao commit/diff. Các dấu nhận việc Markdown chỉ là quy ước phối hợp, không phải khóa kỹ thuật bảo đảm loại trừ.
5. Mặc định chỉ Codex commit/push từ checkout triển khai C:\Users\Dell\bis-ai-project. Antigravity không tự copy toàn bộ thư mục hay push cùng lúc; có thể bàn giao bản vá/commit để tích hợp.
6. Không dùng git reset --hard, clean, stash hoặc xóa file của bên kia để giải quyết xung đột.

## Bàn giao
Mỗi task ghi: mục tiêu, owner, trạng thái, file thay đổi, đầu vào thử, lệnh kiểm tra, kết quả thực tế, giới hạn, việc tiếp theo.
Trạng thái: OPEN → CLAIMED → READY_FOR_REVIEW → VERIFIED. Nếu chặn, ghi BLOCKED kèm dữ liệu cần bổ sung.
READY_FOR_REVIEW chỉ là tác giả đã xong; VERIFIED cần kiểm tra chéo bằng chứng.
Phân biệt test giả lập, API thật, trình duyệt thật và nghiệp vụ đã nghiệm thu.

## Bộ nhớ
Sau cập nhật đã kiểm chứng, cập nhật PROJECT_HANDOVER.md và bài học trong .agents/PROJECT_MEMORY.md rồi chạy:
python sync_memory.py --local-only --record-update "thay đổi đã xác minh; kiểm tra; việc còn lại"
Không tự chỉnh events cũ; dùng MemoryStore để tạo hiệu chỉnh có phiên bản.
Không dùng sync_antigravity_brain.py cho quy trình này: không đọc hoặc sao chép cơ sở dữ liệu IDE, chat riêng, khóa API.
Không đưa task có dữ liệu riêng, chat, memory events, bí mật hoặc backup lên Git.
Google sync hiện chưa xác minh hoạt động; local-only không đồng nghĩa đã đồng bộ Cloud.

## Haravan
Không xóa sản phẩm hiện hữu. Không tự bật HARAVAN_PUSH_ENABLED. Giữ nguyên bảo vệ ngày 20/10/2026, đối soát trùng, duyệt phiên bản và ảnh, published:false cùng các điều kiện bền vững.
Task AI dự phòng hoặc giao diện không được tự thay quyền công cụ Haravan.

## Giới hạn vận hành
Hai công cụ không tự đọc suy nghĩ, hội thoại hoặc phản hồi của nhau. File bàn giao không tự khởi động Antigravity.
Chỉ coi Antigravity đã nhận việc khi nó ghi CLAIMED hoặc có kết quả xác nhận từ chính công cụ.

## Phối hợp theo bằng chứng và điều kiện thực tế
Phân công dưới đây là lựa chọn cho BIS, không phải kết luận một model luôn giỏi hơn model khác. Nếu một công cụ không có quyền trình duyệt/API cần thiết, ghi chặn và chuyển đầu việc phù hợp.

| Chặng | Antigravity phụ trách | Codex phụ trách | Điều kiện nghiệm thu |
|---|---|---|---|
| 1 Gemini | Thử AI Studio và đối chiếu project/model, ghi lỗi đã che khóa | Kiểm tra đường gọi API, phân loại lỗi, tích hợp fallback sau xác minh | Có phản hồi thật; phân biệt local/web; không ghi success giả |
| 2 Technical | Kiểm tra màn hình bằng trình duyệt, thao tác quét/chọn/phạm vi/SKU | Kiểm tra API, lưu trạng thái, dữ liệu theo file/phiên bản và lỗi đồng thời | Cùng file và SKU xuyên suốt; báo cáo có ảnh/bước tái lập |
| 3 Hình ảnh | Đối chiếu ảnh nguồn với benchmark, phát hiện sai SKU/logo/hình khối | Xử lý file, phiên bản, hash ảnh, API chọn ảnh và duyệt | Chủ dự án duyệt chất lượng; test code không thay nghiệm thu ảnh |
| 4 Bộ nhớ và đồng bộ | Kiểm tra mở lại phiên và hiển thị lịch sử | Lưu bền vững, xung đột, backup và xác minh đích sync | Đọc lại khớp sau cập nhật; không mất dữ liệu |
| 5 Haravan | Rà quy trình, nút và thông tin cảnh báo; không thao tác sàn thật | Rà cổng an toàn và test lỗi/đăng lặp bằng giả lập | Mọi rào chắn đạt; không xóa sản phẩm; tác vụ thật có phê duyệt phù hợp |

## Vòng làm việc chung
1. Người làm nhận một nhiệm vụ nhỏ có đầu vào và tiêu chí đạt.
2. Bên phụ trách thực hiện trong phạm vi file đã nhận.
3. Bên còn lại tái lập kiểm tra và ghi PASS/FAIL kèm bằng chứng, không chỉ đọc mô tả của tác giả.
4. Nếu FAIL: trả đúng lỗi về tác giả, không tự sửa trùng file.
5. Codex tích hợp, chạy kiểm tra phù hợp, ghi commit và triển khai sau khi đạt.
6. Antigravity kiểm tra lại giao diện đã triển khai nếu công cụ có quyền. Chưa quan sát thì trạng thái là chưa xác minh.

## Thứ tự ưu tiên hiện tại
P0: Gemini auth/availability → P1: nghiệm thu một trang Technical/SKU thật → P2: đồng bộ Catalogue từ máy lên web và bộ nhớ bền vững → P3: ảnh đúng SKU/chất lượng → P4: mở rộng các phòng ban.
Không mở nhiều bản sửa giao diện trước khi xác minh bản trước trên trình duyệt.
