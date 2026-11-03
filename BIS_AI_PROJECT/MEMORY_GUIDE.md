# Bộ nhớ dài hạn BIS (2026-11-03)

## Đã triển khai
- Nhật ký sự kiện JSON bất biến tại Google_Drive_Storage/8_AI_Memory/events. Mỗi lần sửa tạo phiên bản mới; thu hồi bằng tombstone, không xóa lịch sử.
- Chat các phòng ban gọi Gemini theo GEMINI_MODEL và GEMINI_API_KEY hiện có. Mỗi yêu cầu được lưu trước khi gọi AI. Khi lỗi API, lịch sử vẫn còn, không báo hoàn thành giả.
- Mở lại phiên: nạp 60 tin gần nhất cho mỗi nhân viên; trước câu trả lời nạp kiến thức liên quan và 12 tin gần nhất. Bản xuất chứa toàn bộ lịch sử.
- Ngữ cảnh có giới hạn; lưu lâu dài không có nghĩa nhét toàn bộ kho vào mỗi prompt. Tìm kiếm hiện tại dựa trên từ khóa, chưa phải vector search/OCR toàn bộ PDF.
- Cập nhật nguồn: PROJECT_MEMORY, PROJECT_HANDOVER, feedback_memory, consolidated_rules, marketing_knowledge, knowledge_manifest. Đọc metadata/tri thức đã trích, không tự xác nhận nội dung mọi tài liệu PDF.
- Hiệu chỉnh thủ công ưu tiên hơn snapshot nguồn. Các bản sửa đồng thời được đánh dấu xung đột, không tự chọn theo đồng hồ.
- Marketing tạo lại cache khi dữ liệu sản phẩm/ngữ cảnh thay đổi; Technical nhận ngữ cảnh qua LearningEngine.
- UI tab 8: tìm, thêm, sửa, thu hồi, xem phiên bản, xuất Markdown/JSON, nhập hợp nhất và đồng bộ.
- Lịch sử dùng chung trong dự án BIS hiện có một nhóm tài khoản quản trị; chưa phải hệ thống phân quyền nhiều khách hàng.
- Khung chat tư vấn, chưa chạy các thao tác nghiệp vụ Haravan/dịch file/tạo ảnh. Dùng các tab nghiệp vụ để thực thi.

## Đồng bộ local ↔ Cloud
Đã được chủ dự án xác nhận bảng đích. memory_sync_config.json chứa enabled=true và ID bảng đã duyệt. Có thể ghi đè bằng BIS_MEMORY_SYNC_ENABLED=false để tạm tắt. Local hiện lỗi Invalid JWT Signature: cần cập nhật service account; lỗi đồng bộ hiển thị pending, dữ liệu local không bị xóa.
Dùng worksheet riêng BIS_AI_MEMORY_V1 trong Google Sheets hiện có. Không sửa hàng sản phẩm.
Có thể đặt BIS_MEMORY_SHEET_ID (ID hoặc URL) trong biến môi trường/Streamlit Secrets để dùng bảng riêng.
Mặc định dùng SPREADSHEET_ID_OR_URL, hoặc mở bảng theo SPREADSHEET_NAME; không tự tạo workbook mới.
Service account hiện tại phải có quyền Editor trên bảng đích. Không đưa khóa lên Git.
Khi đã bật: đồng bộ trước khi trả lời sau khi mở ứng dụng, sau thay đổi chat/bộ nhớ, và khi UI hoạt động quá 120 giây kể từ lần đồng bộ trước.
Đây không phải worker chạy nền khi website đã đóng/ngủ. Khi offline: ghi local, hiển thị pending; lần sau hợp nhất theo event ID, không mất lịch sử vì ghi đè.
Nếu Cloud khởi động lại trước khi dữ liệu pending kịp lên Sheets thì dữ liệu chỉ có trên ổ tạm Cloud có thể mất: kiểm tra trạng thái đồng bộ trước khi dừng/redeploy.
Google Drive Desktop đồng bộ các file local theo trạng thái Drive; Google Sheets là cầu nối với Streamlit Cloud.
Không đưa event riêng, backup, lịch sử chat lên GitHub.

## Sau mỗi lần cập nhật dự án
1. Đọc .agents/PROJECT_MEMORY.md, PROJECT_HANDOVER.md và bộ nhớ hiện hành.
2. Sửa code; chạy kiểm thử phù hợp; cập nhật tài liệu bàn giao và bài học.
3. Chạy:
   python sync_memory.py --record-update "Thay đổi đã kiểm tra; giới hạn còn lại; bước tiếp theo"
4. Kiểm tra state=synced (hoặc ghi rõ pending và chạy lại). CURRENT_MEMORY.md được tái tạo để Codex/Antigravity đọc.
5. Chỉ đồng bộ/commit các file code và tài liệu cần thiết. Không git add toàn bộ kho dữ liệu.

Lịch sử của Codex, ChatGPT hoặc Antigravity không tự động trở thành lịch sử trong web BIS.
Dùng bản bàn giao và Markdown xuất từ kho chung khi chuyển công cụ; các chat mới trong BIS được lưu tự động.
Không đọc/ghi cơ sở dữ liệu nội bộ của Antigravity đang mở.

## Gói sử dụng
Theo thông tin chủ dự án: Gemini AI Pro + dung lượng 5 TB, ChatGPT Business.
Dung lượng lưu trữ không tăng cửa sổ ngữ cảnh hay đồng nghĩa API vô hạn.
Ứng dụng hiện tiếp tục dùng Gemini API có sẵn. ChatGPT Business dùng cho công việc ChatGPT/Codex;
OpenAI API cần cấu hình riêng, quyền lợi API credit (nếu đủ điều kiện) phải được xác nhận trên tài khoản.
Chưa thêm khóa OpenAI hoặc phát sinh thuê bao mới.

## Kiểm thử
python -m unittest test_persistent_memory -v
python -m py_compile persistent_memory.py memory_chat.py memory_ui.py sync_memory.py agent_employee_pool.py learning_engine.py agent_marketing.py app_ui.py

Khôi phục: tải JSON từ tab 8; nhập lại để hợp nhất. Import không ghi đè sự kiện cùng ID khác nội dung.
Sao lưu trước nâng cấp nằm trong _memory_upgrade_backup trên máy local.


## Xác minh đợt nâng cấp
- 9 kiểm thử unit và kiểm tra giao diện thêm/sửa/khởi động phiên mới: đạt.
- Bản sao Google Sheets qua kết nối Google Drive: 32 sự kiện đã đọc lại khớp toàn bộ; không sửa tab sản phẩm.
- Đồng bộ tự động Python local: chưa chạy được vì Invalid JWT Signature của service account hiện có.
- Kiểm tra Gemini thật: API trả 503 UNAVAILABLE do model quá tải; không phải bằng chứng sai API key. Chat lưu yêu cầu trước khi gọi AI và thông báo lỗi rõ khi chưa có phản hồi.
- Bản code đã chuẩn bị ở ổ G và bản Git local. Chủ dự án đã duyệt commit/push lên main để triển khai Streamlit. Kiểm tra trạng thái deploy thực tế trước khi tuyên bố tất cả chức năng online đã chạy.
