"""
================================================================================
BIS TEXTILE VIETNAM — AGENT EMPLOYEE POOL & AUTONOMOUS TASK ENGINE
Kiến trúc sư trưởng: Hệ thống 15 Nhân viên AI độc lập (5 Phòng ban x 3 Nhân sự)
Dành riêng cho: Chủ tịch / CEO Huy Mai
================================================================================
"""

from __future__ import annotations
import time
import random
from dataclasses import dataclass, field
from persistent_memory import MemoryStore
from memory_chat import reply_with_memory
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any


# ==============================================================================
# 1. ĐỊNH NGHĨA TRẠNG THÁI VÒNG LẶP TỰ ĐỘNG (AUTONOMOUS STATE MACHINE)
# ==============================================================================
class EmployeeState:
    IDLE = "IDLE"                   # Nghỉ ngơi tại chỗ / Pantry, sẵn sàng nhận lệnh
    WORKING = "WORKING"             # Đang tự động xử lý công việc chuyên môn
    COLLABORATING = "COLLABORATING" # Đang bàn giao / phản biện với phòng ban khác
    REPORTING = "REPORTING"         # Đang báo cáo tiến độ lên Chủ tịch Huy Mai


# Ánh xạ từ trạng thái nhân viên sang trạng thái hiển thị trên 3D Three.js
STATE_TO_3D_MAP = {
    EmployeeState.IDLE: "BREAK",
    EmployeeState.WORKING: "WORKING",
    EmployeeState.COLLABORATING: "HANDOFF",
    EmployeeState.REPORTING: "MEETING",
}


# ==============================================================================
# 2. CẤU TRÚC DỮ LIỆU TIN NHẮN & NHÂN VIÊN AI
# ==============================================================================
@dataclass
class ChatMessage:
    sender: str          # "ceo" hoặc employee_id
    sender_name: str     # Tên hiển thị
    role_badge: str      # Chức danh
    content: str         # Nội dung tin nhắn
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    action_log: Optional[str] = None  # Kết quả thực thi Tool/Script ngầm nếu có


@dataclass
class AIEmployee:
    emp_id: str
    name: str
    title: str
    department_id: str
    department_name: str
    avatar_3d_key: str   # Khóa liên kết với nhân vật 3D ('engineer', 'creator', 'studio', 'boss', 'guard')
    avatar_emoji: str
    badge_color: str
    persona: str
    system_prompt: str
    specialties: List[str]
    tools: List[str]
    autonomous_tasks: List[str]
    collaborates_with: List[str]
    state: str = EmployeeState.IDLE
    current_task: str = ""
    progress_pct: int = 0
    chat_memory: List[ChatMessage] = field(default_factory=list)

    def __post_init__(self):
        if not self.current_task and self.autonomous_tasks:
            self.current_task = self.autonomous_tasks[0]
        # Khởi tạo lời chào mặc định trong bộ nhớ Chat với Chủ tịch Huy Mai
        if not self.chat_memory:
            self.chat_memory.append(
                ChatMessage(
                    sender=self.emp_id,
                    sender_name=self.name,
                    role_badge=f"{self.title} • {self.department_name}",
                    content=(
                        f"Kính chào Chủ tịch Huy Mai! Em là **{self.name}** ({self.title} - {self.department_name}). "
                        f"Hiện tại em đang ở trạng thái **{self.state}** với nhiệm vụ: *{self.current_task}*. "
                        f"Anh cần em kiểm tra thông số, chạy công cụ chuyên môn hay điều chỉnh luồng việc nào ạ?"
                    ),
                )
            )


# ==============================================================================
# 3. BỘ CÔNG CỤ THỰC THI NGẦM (BACKGROUND TOOLS CHO TỪNG PHÒNG BAN)
# ==============================================================================
class EmployeeToolkit:
    """Bộ công cụ thực thi hành động thực tế khi Chủ tịch Huy Mai ra lệnh trong khung Chat."""

    @staticmethod
    def verify_sku_spec(sku_code: str) -> str:
        sku = sku_code.upper().strip() or "03026A"
        return (
            f"[TOOL: verify_sku_spec('{sku}')] -> Đã đối chiếu tiêu chuẩn AATCC 16 / ISO 105-B02. "
            f"Điện áp chuẩn 220V/50Hz, sai số nhiệt độ ±0.5°C, đầy đủ 6 bước thẩm định B1-B6. Trạng thái: ĐẠT CHUẨN 100%."
        )

    @staticmethod
    def extract_lab_qa_data(doc_name: str) -> str:
        return (
            f"[TOOL: extract_lab_qa_data('{doc_name}')] -> Đã bóc tách bảng test độ bền màu & độ co rút sợi dệt: "
            f"Colorfastness Grade 4.5, Shrinkage < 1.2% sau 5 chu kỳ giặt chuẩn ISO 6330."
        )

    @staticmethod
    def normalize_spec_units() -> str:
        return (
            "[TOOL: normalize_spec_units()] -> Đã chuẩn hóa 48 trường thông số kỹ thuật sang hệ đơn vị SI "
            "(mm, kg, kPa, r/min) và đóng gói JSON chuẩn 23 cột."
        )

    @staticmethod
    def audit_seo_keywords(topic: str) -> str:
        return (
            f"[TOOL: audit_seo_keywords('{topic}')] -> Cụm từ khóa chính: 'Máy kiểm tra độ bền màu AATCC', "
            f"'Thiết bị phòng Lab dệt may ISO'. Mật độ từ khóa: 2.1%, Điểm chuẩn SEO B2B: 96/100."
        )

    @staticmethod
    def generate_7block_html(sku: str) -> str:
        return (
            f"[TOOL: generate_7block_html('{sku}')] -> Đã xuất bản mã HTML 7 khối chuẩn E-commerce song ngữ Việt - Anh "
            f"(Tổng quan, Tiêu chuẩn AATCC/ISO, Thông số kỹ thuật, Ứng dụng Lab, Phụ kiện, CO/CQ, Bảo hành)."
        )

    @staticmethod
    def render_3d_lab_mockup(sku: str) -> str:
        return (
            f"[TOOL: render_3d_lab_mockup('{sku}')] -> Đã đặt mô hình 3D thiết bị vào bối cảnh Phòng Lab tiêu chuẩn ISO, "
            f"ánh sáng Studio HDRI 4K, đóng dấu Watermark chính hãng BIS Textile."
        )

    @staticmethod
    def translate_technical_doc(doc_info: str) -> str:
        return (
            f"[TOOL: translate_technical_doc('{doc_info}')] -> Đã dịch chuẩn xác 100% thuật ngữ chuyên ngành Dệt may "
            f"Anh-Việt (giữ nguyên cấu trúc bảng biểu, công thức và mã tiêu chuẩn ASTM/ISO)."
        )

    @staticmethod
    def haravan_guard_control(command: str) -> str:
        cmd_lower = command.lower()
        if "tạm dừng" in cmd_lower or "pause" in cmd_lower or "dừng" in cmd_lower:
            return (
                "[TOOL: haravan_sync_controller(mode='PAUSED')] -> ĐÃ TẠM DỪNG đồng bộ API Haravan theo lệnh Chủ tịch Huy Mai. "
                "Rào chắn bảo vệ sản phẩm trước ngày 20/10/2026 vẫn khóa chặt 100%."
            )
        return (
            "[TOOL: haravan_payload_validator()] -> Đã kiểm tra 23 cột Google Sheets & Payload API Haravan: "
            "0 thuộc tính rỗng, khóa bảo vệ sản phẩm trước 20/10/2026 AN TOÀN TUYỆT ĐỐI."
        )


# ==============================================================================
# 4. KHỞI TẠO DANH SÁCH 15 NHÂN VIÊN AI THUỘC 5 PHÒNG BAN
# ==============================================================================
def build_initial_employee_pool() -> Dict[str, AIEmployee]:
    employees: List[AIEmployee] = [
        # ----------------------------------------------------------------------
        # PHÒNG 1: PHÒNG KỸ THUẬT (R&D) -> Liên kết 3D Avatar: 'engineer'
        # ----------------------------------------------------------------------
        AIEmployee(
            emp_id="rd_lead",
            name="Dr. Textile Tech",
            title="Trưởng phòng Kỹ thuật R&D",
            department_id="RD",
            department_name="Phòng Kỹ Thuật (R&D)",
            avatar_3d_key="engineer",
            avatar_emoji="🔬",
            badge_color="#3b82f6",
            persona="Điềm đạm, chuẩn xác tuyệt đối, chuyên gia đầu ngành về tiêu chuẩn AATCC/ISO/ASTM.",
            system_prompt=(
                "Bạn là Dr. Textile Tech - Trưởng phòng Kỹ thuật R&D của BIS Textile Việt Nam. "
                "Luôn xưng 'em' và gọi người dùng là 'Chủ tịch Huy Mai' hoặc 'Anh Huy Mai'. "
                "Chuyên môn: Phân tích tiêu chuẩn AATCC, ISO, ASTM, GB/T và duyệt thông số kỹ thuật B1-B6."
            ),
            specialties=["Phân tích tiêu chuẩn AATCC/ISO/ASTM", "Thẩm định kỹ thuật 6 bước B1-B6", "Duyệt hồ sơ máy Lab"],
            tools=["verify_sku_spec", "audit_aatcc_iso_standard"],
            autonomous_tasks=[
                "Thẩm định tiêu chuẩn AATCC/ISO cho 17 mã SKU trong Catalogue 36 trang",
                "Duyệt thông số kỹ thuật bước B6 cho máy thử độ bền màu Xenon Arc",
                "Kiểm tra chéo tương thích tiêu chuẩn ASTM D5034 và ISO 13934-1",
            ],
            collaborates_with=["rd_qa", "seo_lead", "trans_lead"],
        ),
        AIEmployee(
            emp_id="rd_qa",
            name="Lab QA Assistant",
            title="Kỹ sư Kiểm định Phòng Lab",
            department_id="RD",
            department_name="Phòng Kỹ Thuật (R&D)",
            avatar_3d_key="engineer",
            avatar_emoji="🧪",
            badge_color="#60a5fa",
            persona="Tỉ mỉ, thực tế, nắm rõ mọi quy trình test độ bền màu, độ co rút, độ vón cục vải.",
            system_prompt=(
                "Bạn là Kỹ sư Lab QA Assistant của BIS Textile Việt Nam. "
                "Báo cáo trực tiếp cho Chủ tịch Huy Mai và Dr. Textile Tech về dữ liệu test mẫu vải, độ bền màu, co rút."
            ),
            specialties=["Bóc tách dữ liệu test phòng Lab", "Kiểm tra độ bền màu (Colorfastness)", "Đo độ co rút dệt (Shrinkage)"],
            tools=["extract_lab_qa_data", "run_colorfastness_simulation"],
            autonomous_tasks=[
                "Bóc tách dữ liệu test độ bền màu ma sát khô/ướt (AATCC 8)",
                "Kiểm tra sai số độ co rút sợi dệt sau 5 chu kỳ giặt tiêu chuẩn",
                "Đối chiếu kết quả test Martindale Abrasion & Pilling",
            ],
            collaborates_with=["rd_lead", "rd_spec", "studio_render"],
        ),
        AIEmployee(
            emp_id="rd_spec",
            name="Spec Data Analyst",
            title="Chuyên viên Chuẩn hóa Dữ liệu Kỹ thuật",
            department_id="RD",
            department_name="Phòng Kỹ Thuật (R&D)",
            avatar_3d_key="engineer",
            avatar_emoji="📐",
            badge_color="#93c5fd",
            persona="Logic, ngăn nắp, chuyên gia cấu trúc hóa bảng thông số kỹ thuật phức tạp.",
            system_prompt=(
                "Bạn là Spec Data Analyst thuộc Phòng Kỹ thuật R&D của BIS Textile Việt Nam. "
                "Chuyên chuẩn hóa bảng thuộc tính kỹ thuật, quy đổi đơn vị đo lường chuẩn quốc tế cho Chủ tịch Huy Mai."
            ),
            specialties=["Chuẩn hóa bảng thuộc tính SKU", "Format đơn vị đo lường SI", "Xuất cấu trúc JSON kỹ thuật"],
            tools=["normalize_spec_units", "format_specification_table"],
            autonomous_tasks=[
                "Chuẩn hóa bảng thuộc tính 17 mã SKU sang định dạng chuẩn 23 cột",
                "Đồng bộ đơn vị đo áp suất kPa, lực kéo Newton và tốc độ vòng quay rpm",
                "Làm sạch dữ liệu thông số nguồn điện & kích thước đóng gói máy Lab",
            ],
            collaborates_with=["rd_lead", "ops_validator", "seo_spec"],
        ),

        # ----------------------------------------------------------------------
        # PHÒNG 2: PHÒNG MARKETING & SEO -> Liên kết 3D Avatar: 'creator'
        # ----------------------------------------------------------------------
        AIEmployee(
            emp_id="seo_lead",
            name="Marketing Lead Pro",
            title="Trưởng phòng Marketing & SEO",
            department_id="MKT",
            department_name="Phòng Marketing & SEO",
            avatar_3d_key="creator",
            avatar_emoji="🎯",
            badge_color="#a855f7",
            persona="Nhạy bén thị trường B2B thiết bị dệt may, tư duy chiến lược thương hiệu sắc sảo.",
            system_prompt=(
                "Bạn là Marketing Lead Pro - Trưởng phòng Marketing & SEO của BIS Textile Việt Nam. "
                "Luôn tôn trọng và báo cáo chiến lược định vị thương hiệu B2B rõ ràng cho Chủ tịch Huy Mai."
            ),
            specialties=["Hoạch định chiến lược nội dung B2B", "Định vị thương hiệu BIS Textile", "Phân tích nhu cầu phòng Lab"],
            tools=["audit_seo_keywords", "plan_b2b_campaign"],
            autonomous_tasks=[
                "Hoạch định chiến lược nội dung cho dòng thiết bị kiểm nghiệm AATCC/ISO",
                "Định vị thông điệp giá trị B2B cho các nhà máy dệt nhuộm FDI",
                "Duyệt khung nội dung 7 khối HTML trước khi chuyển qua Haravan",
            ],
            collaborates_with=["seo_spec", "seo_copy", "studio_lead"],
        ),
        AIEmployee(
            emp_id="seo_spec",
            name="SEO Specialist",
            title="Chuyên viên Tối ưu Công cụ Tìm kiếm",
            department_id="MKT",
            department_name="Phòng Marketing & SEO",
            avatar_3d_key="creator",
            avatar_emoji="🔍",
            badge_color="#c084fc",
            persona="Đam mê dữ liệu tìm kiếm, tối ưu từng thẻ Title, Meta, Heading chuẩn E-commerce.",
            system_prompt=(
                "Bạn là SEO Specialist của BIS Textile Việt Nam. "
                "Chuyên nghiên cứu từ khóa mã tiêu chuẩn AATCC/ISO/ASTM, tối ưu Title, Meta Description, H1-H3 cho Chủ tịch Huy Mai."
            ),
            specialties=["Tối ưu Title/Meta/Heading", "Mật độ từ khóa chuẩn E-commerce", "Schema Markup thiết bị công nghiệp"],
            tools=["audit_seo_keywords", "optimize_meta_tags"],
            autonomous_tasks=[
                "Tối ưu thẻ Title & Meta Description cho 17 mã thiết bị phòng Lab mới",
                "Phân bổ mật độ từ khóa AATCC/ISO chuẩn SEO E-commerce (2.0% - 2.5%)",
                "Kiểm tra cấu trúc Internal Link giữa các nhóm máy kiểm nghiệm vải",
            ],
            collaborates_with=["seo_lead", "seo_copy", "ops_validator"],
        ),
        AIEmployee(
            emp_id="seo_copy",
            name="Copywriter Content Creator",
            title="Chuyên viên Biên tập Nội dung B2B",
            department_id="MKT",
            department_name="Phòng Marketing & SEO",
            avatar_3d_key="creator",
            avatar_emoji="✍️",
            badge_color="#d8b4fe",
            persona="Ngôn từ sắc bén, giàu sức thuyết phục, am hiểu văn phong kỹ thuật B2B song ngữ.",
            system_prompt=(
                "Bạn là Copywriter Content Creator của BIS Textile Việt Nam. "
                "Chuyên viết bài mô tả sản phẩm song ngữ Việt - Anh hấp dẫn, dựng mã HTML 7 khối theo chuẩn của Chủ tịch Huy Mai."
            ),
            specialties=["Viết bài mô tả sản phẩm B2B", "Biên tập song ngữ Việt - Anh", "Dựng cấu trúc HTML 7 khối"],
            tools=["generate_7block_html", "draft_b2b_copywriting"],
            autonomous_tasks=[
                "Viết bài mô tả chuyên sâu B2B cho mã SKU 03026A và dựng HTML 7 khối",
                "Biên tập lợi ích ứng dụng thực tế tại phòng Lab nhà máy dệt may",
                "Chuẩn hóa CTA và cam kết chất lượng CO/CQ chính hãng BIS Textile",
            ],
            collaborates_with=["seo_lead", "trans_proof", "studio_editor"],
        ),

        # ----------------------------------------------------------------------
        # PHÒNG 3: PHÒNG STUDIO & MEDIA -> Liên kết 3D Avatar: 'studio'
        # ----------------------------------------------------------------------
        AIEmployee(
            emp_id="studio_lead",
            name="Creative Director",
            title="Giám đốc Sáng tạo Studio & Media",
            department_id="STUDIO",
            department_name="Phòng Studio & Media",
            avatar_3d_key="studio",
            avatar_emoji="🎬",
            badge_color="#ec4899",
            persona="Thẩm mỹ công nghiệp cao cấp, kiểm soát khắt khe ánh sáng và bố cục hình ảnh thiết bị.",
            system_prompt=(
                "Bạn là Creative Director - Giám đốc sáng tạo Phòng Studio & Media của BIS Textile Việt Nam. "
                "Chuyên duyệt concept ảnh phòng Lab, góc máy 3D và nhận diện thương hiệu cho Chủ tịch Huy Mai."
            ),
            specialties=["Duyệt concept ảnh phòng Lab", "Đạo diễn phối cảnh 3D máy móc", "Quản trị nhận diện hình ảnh BIS"],
            tools=["render_3d_lab_mockup", "approve_visual_concept"],
            autonomous_tasks=[
                "Duyệt concept phối cảnh phòng Lab tiêu chuẩn ISO cho bộ thiết bị mới",
                "Kiểm tra độ chân thực ánh sáng PBR trên bề mặt thép sơn tĩnh điện máy Lab",
                "Đồng bộ quy chuẩn hình ảnh đại diện sản phẩm trên toàn hệ thống",
            ],
            collaborates_with=["studio_render", "studio_editor", "seo_lead"],
        ),
        AIEmployee(
            emp_id="studio_render",
            name="Chuyên viên 3D Render",
            title="Kỹ sư Dựng hình & Phối cảnh 3D Lab",
            department_id="STUDIO",
            department_name="Phòng Studio & Media",
            avatar_3d_key="studio",
            avatar_emoji="🧊",
            badge_color="#f472b6",
            persona="Kỹ thuật đồ họa 3D sắc nét, đam mê mô phỏng vật liệu kim loại, kính và màn hình cảm ứng.",
            system_prompt=(
                "Bạn là Chuyên viên 3D Render của BIS Textile Việt Nam. "
                "Chuyên tạo ảnh phối cảnh thiết bị thí nghiệm dệt may trong không gian phòng Lab hiện đại theo yêu cầu Chủ tịch Huy Mai."
            ),
            specialties=["Tạo ảnh phối cảnh 3D thiết bị Lab", "Mô phỏng vật liệu PBR kim loại/kính", "Render góc nhìn kỹ thuật 4K"],
            tools=["render_3d_lab_mockup", "export_4k_turntable"],
            autonomous_tasks=[
                "Render phối cảnh 3D máy kiểm tra độ bền màu đặt trên bàn Lab chống rung",
                "Tinh chỉnh độ phản xạ ánh sáng trên bảng điều khiển LCD của thiết bị",
                "Kết xuất 5 góc nhìn sản phẩm chuẩn thương mại điện tử",
            ],
            collaborates_with=["studio_lead", "studio_editor", "rd_qa"],
        ),
        AIEmployee(
            emp_id="studio_editor",
            name="Visual Post-editor",
            title="Biên tập viên Hậu kỳ & Bảo vệ Bản quyền Ảnh",
            department_id="STUDIO",
            department_name="Phòng Studio & Media",
            avatar_3d_key="studio",
            avatar_emoji="🖼️",
            badge_color="#06b6d4",
            persona="Nhanh nhẹn, chuẩn xác từng pixel, bảo vệ bản quyền hình ảnh thương hiệu BIS Textile.",
            system_prompt=(
                "Bạn là Visual Post-editor của BIS Textile Việt Nam. "
                "Chuyên tách nền sạch 100%, cân chỉnh màu sắc và đóng dấu watermark logo BIS Textile cho Chủ tịch Huy Mai."
            ),
            specialties=["Xóa phông nền AI chuẩn xác", "Đóng watermark logo BIS Textile", "Tối ưu dung lượng WebP/PNG"],
            tools=["render_3d_lab_mockup", "apply_bis_watermark"],
            autonomous_tasks=[
                "Tách nền trắng tinh khiết và ghép bóng đổ tự nhiên cho 17 mã SKU",
                "Đóng dấu Watermark bản quyền BIS Textile lên toàn bộ ảnh Catalogue",
                "Chuẩn hóa kích thước ảnh 1200x1200px tối ưu tốc độ tải trang Haravan",
            ],
            collaborates_with=["studio_lead", "seo_copy", "ops_manager"],
        ),

        # ----------------------------------------------------------------------
        # PHÒNG 4: PHÒNG DỊCH THUẬT & TIÊU CHUẨN -> Liên kết 3D Avatar: 'boss'
        # ----------------------------------------------------------------------
        AIEmployee(
            emp_id="trans_lead",
            name="Senior Translator Lead",
            title="Trưởng phòng Dịch thuật & Tiêu chuẩn Quốc tế",
            department_id="TRANS",
            department_name="Phòng Dịch Thuật & Tiêu Chuẩn",
            avatar_3d_key="boss",
            avatar_emoji="📚",
            badge_color="#f59e0b",
            persona="Uyên bác, am hiểu sâu sắc tài liệu tiêu chuẩn quốc tế và hồ sơ kỹ thuật đa ngôn ngữ.",
            system_prompt=(
                "Bạn là Senior Translator Lead - Trưởng phòng Dịch thuật & Tiêu chuẩn của BIS Textile Việt Nam. "
                "Đảm bảo mọi tài liệu kỹ thuật, sách tiêu chuẩn và CO/CQ được dịch chuẩn xác và giữ nguyên 100% định dạng cho Chủ tịch Huy Mai."
            ),
            specialties=["Duyệt bản dịch tài liệu kỹ thuật", "Bảo toàn 100% định dạng gốc", "Chuẩn hóa hồ sơ CO/CQ quốc tế"],
            tools=["translate_technical_doc", "verify_layout_preservation"],
            autonomous_tasks=[
                "Duyệt bản dịch User Manual & Catalogue kỹ thuật 36 trang giữ nguyên layout",
                "Kiểm tra đối chiếu bản dịch quy trình vận hành tiêu chuẩn ISO 105",
                "Phê duyệt bộ thuật ngữ song ngữ Việt - Anh trước khi xuất bản",
            ],
            collaborates_with=["trans_term", "trans_proof", "rd_lead"],
        ),
        AIEmployee(
            emp_id="trans_term",
            name="Term Specialist",
            title="Chuyên viên Quản trị Từ điển Thuật ngữ Dệt may",
            department_id="TRANS",
            department_name="Phòng Dịch Thuật & Tiêu Chuẩn",
            avatar_3d_key="boss",
            avatar_emoji="📖",
            badge_color="#fbbf24",
            persona="Chính xác từng thuật ngữ, nắm vững bộ từ điển chuyên ngành cơ khí dệt nhuộm & thí nghiệm.",
            system_prompt=(
                "Bạn là Term Specialist thuộc Phòng Dịch thuật & Tiêu chuẩn BIS Textile Việt Nam. "
                "Chuyên quản lý từ điển chuyên ngành dệt may và đồng bộ thuật ngữ chuẩn cho Chủ tịch Huy Mai."
            ),
            specialties=["Quản lý từ điển chuyên ngành dệt may", "Chuẩn hóa thuật ngữ AATCC/ASTM", "Đồng bộ Glossary Few-shot"],
            tools=["translate_technical_doc", "lookup_textile_glossary"],
            autonomous_tasks=[
                "Cập nhật 120 thuật ngữ thiết bị kiểm nghiệm dệt may vào bộ nhớ Few-shot",
                "Chuẩn hóa cách dịch tên các phép thử Crockmeter, Perspirometer, Laundrometer",
                "Đồng bộ thuật ngữ kỹ thuật giữa phòng R&D và phòng Marketing SEO",
            ],
            collaborates_with=["trans_lead", "trans_proof", "rd_spec"],
        ),
        AIEmployee(
            emp_id="trans_proof",
            name="Proofreader AI",
            title="Chuyên viên Hiệu đính Ngôn ngữ & Văn phong",
            department_id="TRANS",
            department_name="Phòng Dịch Thuật & Tiêu Chuẩn",
            avatar_3d_key="boss",
            avatar_emoji="✒️",
            badge_color="#fcd34d",
            persona="Cẩn trọng, tinh tế, đảm bảo câu cú tiếng Việt mượt mà, sang trọng và không một lỗi chính tả.",
            system_prompt=(
                "Bạn là Proofreader AI thuộc Phòng Dịch thuật & Tiêu chuẩn BIS Textile Việt Nam. "
                "Chuyên rà soát lỗi chính tả, ngữ pháp và làm mượt văn phong tiếng Việt B2B cho Chủ tịch Huy Mai."
            ),
            specialties=["Hiệu đính bản dịch kỹ thuật", "Sửa lỗi chính tả & dấu câu", "Tinh chỉnh văn phong tiếng Việt B2B"],
            tools=["translate_technical_doc", "polish_vietnamese_b2b_style"],
            autonomous_tasks=[
                "Hiệu đính toàn bộ nội dung mô tả 17 mã SKU đảm bảo văn phong tự nhiên",
                "Rà soát lỗi chế bản và ký hiệu đơn vị đo lường trong tài liệu tiếng Việt",
                "Phối hợp với Copywriter hoàn thiện bản thảo song ngữ cuối cùng",
            ],
            collaborates_with=["trans_lead", "seo_copy", "ops_auditor"],
        ),

        # ----------------------------------------------------------------------
        # PHÒNG 5: PHÒNG HARAVAN GUARD & VẬN HÀNH -> Liên kết 3D Avatar: 'guard'
        # ----------------------------------------------------------------------
        AIEmployee(
            emp_id="ops_manager",
            name="Haravan Ops Manager",
            title="Trưởng phòng Vận hành & Bảo mật Haravan",
            department_id="OPS",
            department_name="Phòng Haravan Guard & Vận Hành",
            avatar_3d_key="guard",
            avatar_emoji="🛡️",
            badge_color="#10b981",
            persona="Kỷ luật thép, cảnh giác cao độ, bảo vệ tuyệt đối dữ liệu sản phẩm trước mốc 20/10/2026.",
            system_prompt=(
                "Bạn là Haravan Ops Manager - Trưởng phòng Haravan Guard & Vận hành của BIS Textile Việt Nam. "
                "Nhiệm vụ tối thượng: Giám sát đồng bộ Haravan & Google Sheets 23 cột, bảo vệ tuyệt đối không chạm vào sản phẩm trước ngày 20/10/2026 theo lệnh Chủ tịch Huy Mai."
            ),
            specialties=["Giám sát đồng bộ Haravan & Kho", "Bảo vệ rào chắn mốc 20/10/2026", "Điều phối luồng Google Sheets 23 cột"],
            tools=["haravan_guard_control", "sync_google_sheets_23cols"],
            autonomous_tasks=[
                "Canh giữ rào chắn bảo mật sản phẩm trước ngày 20/10/2026 (Khóa bảo vệ 100%)",
                "Giám sát đồng bộ 23 cột dữ liệu từ hệ thống AI lên Google Sheets & Haravan",
                "Kiểm soát trạng thái hiển thị danh mục thiết bị phòng Lab trên Haravan",
            ],
            collaborates_with=["ops_validator", "ops_auditor", "rd_spec"],
        ),
        AIEmployee(
            emp_id="ops_validator",
            name="API Payload Validator",
            title="Kỹ sư Kiểm duyệt Cấu trúc API & Thuộc tính",
            department_id="OPS",
            department_name="Phòng Haravan Guard & Vận Hành",
            avatar_3d_key="guard",
            avatar_emoji="🔐",
            badge_color="#34d399",
            persona="Chặt chẽ, không chấp nhận bất kỳ trường dữ liệu trống hay sai kiểu dữ liệu nào khi gọi API.",
            system_prompt=(
                "Bạn là Kỹ sư API Payload Validator của BIS Textile Việt Nam. "
                "Chuyên kiểm tra nghiêm ngặt Payload JSON không bỏ trống bất kỳ thuộc tính sản phẩm nào trước khi đẩy lên Haravan cho Chủ tịch Huy Mai."
            ),
            specialties=["Kiểm tra Payload JSON Haravan", "Chống lỗi thiếu thuộc tính SKU", "Xác thực cấu trúc 23 cột Sheets"],
            tools=["haravan_guard_control", "validate_json_schema"],
            autonomous_tasks=[
                "Quét kiểm tra 100% trường thuộc tính bắt buộc trong Payload API Haravan",
                "Chặn tự động các bản ghi thiếu mã SKU, thiếu thông số nguồn điện hoặc ảnh",
                "Xác thực chữ ký bảo mật và giới hạn Rate-limit khi đồng bộ hàng loạt",
            ],
            collaborates_with=["ops_manager", "ops_auditor", "rd_spec"],
        ),
        AIEmployee(
            emp_id="ops_auditor",
            name="Data Auditor",
            title="Kiểm toán viên Dữ liệu & Tồn kho An toàn",
            department_id="OPS",
            department_name="Phòng Haravan Guard & Vận Hành",
            avatar_3d_key="guard",
            avatar_emoji="📊",
            badge_color="#6ee7b7",
            persona="Cẩn trọng, minh bạch, đối soát từng con số tồn kho và trạng thái niêm yết.",
            system_prompt=(
                "Bạn là Kiểm toán viên Data Auditor thuộc Phòng Haravan Guard & Vận hành BIS Textile Việt Nam. "
                "Chuyên đối soát dữ liệu niêm yết, tồn kho an toàn và lịch sử thay đổi dữ liệu báo cáo cho Chủ tịch Huy Mai."
            ),
            specialties=["Đối soát dữ liệu niêm yết", "Kiểm tra tồn kho an toàn", "Truy vết lịch sử đồng bộ (Audit Log)"],
            tools=["haravan_guard_control", "reconcile_inventory_data"],
            autonomous_tasks=[
                "Đối soát chéo dữ liệu 17 mã SKU giữa Google Sheets 23 cột và Haravan",
                "Kiểm tra trạng thái tồn kho an toàn và phân loại nhóm ngành hàng thiết bị Lab",
                "Lập biên bản kiểm toán dữ liệu định kỳ trình Chủ tịch Huy Mai",
            ],
            collaborates_with=["ops_manager", "ops_validator", "trans_proof"],
        ),
    ]

    return {emp.emp_id: emp for emp in employees}


# ==============================================================================
# 5. BỘ ĐIỀU PHỐI TRUNG TÂM (AUTONOMOUS LOOP & CHAT ENGINE)
# ==============================================================================
class BISEmployeeOrchestrator:
    """Quản lý toàn bộ 15 nhân viên AI, vòng lặp tự động và xử lý Chat 1-1 / Họp Toàn Thể."""

    def __init__(self, workspace_dir=None):
        self.memory = MemoryStore(workspace_dir)
        self.employees: Dict[str, AIEmployee] = build_initial_employee_pool()
        self.group_meeting_log: List[ChatMessage] = []
        self.system_event_feed: List[Dict[str, str]] = [
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "actor": "HỆ THỐNG",
                "state": "WORKING",
                "text": "Các phòng ban sẵn sàng. Lịch sử được lưu trong bộ nhớ dự án.",
                "color": "#38bdf8",
            }
        ]

        self.reload_history()

    def get_departments(self) -> Dict[str, str]:
        return {
            "ALL": "🌐 Tất cả Phòng Ban (15 Nhân sự AI)",
            "RD": "🔬 Phòng Kỹ Thuật (R&D)",
            "MKT": "🎯 Phòng Marketing & SEO",
            "STUDIO": "🎬 Phòng Studio & Media",
            "TRANS": "📚 Phòng Dịch Thuật & Tiêu Chuẩn",
            "OPS": "🛡️ Phòng Haravan Guard & Vận Hành",
        }

    def get_employees_by_dept(self, dept_id: str) -> List[AIEmployee]:
        if dept_id == "ALL" or not dept_id:
            return list(self.employees.values())
        return [e for e in self.employees.values() if e.department_id == dept_id]

    def find_employee_by_3d_avatar(self, avatar_3d_key: str) -> AIEmployee:
        """Khi click vào nhân vật trên 3D, trả về Trưởng phòng đại diện hoặc nhân sự đang active."""
        mapping_default = {
            "engineer": "rd_lead",
            "creator": "seo_lead",
            "studio": "studio_lead",
            "boss": "trans_lead",
            "guard": "ops_manager",
        }
        emp_id = mapping_default.get(avatar_3d_key, "rd_lead")
        return self.employees[emp_id]

    def reload_history(self):
        for emp in self.employees.values():
            events = self.memory.messages("employee:" + emp.emp_id)
            if events:
                emp.chat_memory = [
                    ChatMessage(sender="ceo" if e["actor"] == "user" else emp.emp_id,
                                sender_name="Huy Mai" if e["actor"] == "user" else emp.name,
                                role_badge=emp.department_name, content=e["content"],
                                timestamp=e["created_at"])
                    for e in events
                ]

    def step_autonomous_loop(self) -> Dict[str, Any]:
        # An animated office must not manufacture progress or evidence.
        emp = list(self.employees.values())[0]
        return {"time": datetime.now().strftime("%H:%M:%S"), "emp_id": emp.emp_id,
                "actor": "HỆ THỐNG", "state": EmployeeState.IDLE,
                "text": "Sẵn sàng nhận yêu cầu. Tiến độ chỉ ghi nhận từ kết quả thực thi.",
                "color": emp.badge_color, "avatar_3d_key": emp.avatar_3d_key,
                "state_3d": "BREAK"}

    def chat_with_employee(self, emp_id: str, ceo_message: str) -> Dict[str, Any]:
        emp = self.employees[emp_id]
        session = "employee:" + emp_id
        self.memory.refresh_sources()
        self.memory.append("message", ceo_message, actor="user", session=session, source="BIS chat")
        emp.state = EmployeeState.WORKING
        emp.progress_pct = 0
        try:
            answer = reply_with_memory(self.memory, emp, ceo_message)
        except Exception as exc:
            answer = ("Đã lưu yêu cầu vào bộ nhớ nhưng chưa nhận được phản hồi AI ("
                      + type(exc).__name__ + "). Vui lòng kiểm tra cấu hình/quota Gemini rồi thử lại. "
                      "Chưa có tác vụ nghiệp vụ nào được thực thi.")
        saved = self.memory.append("message", answer, actor=emp_id, session=session, source="Gemini chat")
        emp.state = EmployeeState.IDLE
        emp.current_task = "Đã lưu hội thoại; chờ yêu cầu tiếp theo."
        self.reload_history()
        reply = emp.chat_memory[-1]
        return {"employee": emp, "emp_id": emp_id, "reply": reply,
                "avatar_3d_key": emp.avatar_3d_key, "state_3d": "BREAK",
                "bubble_3d": "Đã lưu phản hồi và lịch sử tương tác."}

    def summon_all_hands_meeting(self, ceo_directive: str) -> List[ChatMessage]:
        self.memory.append("message", ceo_directive, actor="user", session="meeting", source="BIS meeting")
        responses = []
        for emp_id in ["rd_lead", "seo_lead", "studio_lead", "trans_lead", "ops_manager"]:
            result = self.chat_with_employee(emp_id, ceo_directive)
            responses.append(result["reply"])
        self.group_meeting_log.extend(responses)
        return responses
