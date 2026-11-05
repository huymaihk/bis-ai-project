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
