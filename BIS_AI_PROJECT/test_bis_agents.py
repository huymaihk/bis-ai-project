"""
BIS Textile AI Multi-Agent Platform - DeepEval Test Suite
Automated Quality Assurance for Agent_Technical 6-Step Verification Pipeline (B1 - B6)
and Haravan 7-Block Technical Description Synthesis.
"""
import os
import sys
import json
import pytest
from pathlib import Path

# Thêm đường dẫn workspace vào sys.path
WORKSPACE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(WORKSPACE_DIR))

import deepeval
from deepeval.test_case import LLMTestCase
from deepeval.metrics import BaseMetric
from deepeval import assert_test

from agent_technical import AgentTechnical


# ══════════════════════════════════════════════════════════════════════════════
# 1. CÁC ĐỘ ĐO DEEPEVAL CHO TỪNG BƯỚC THẨM ĐỊNH KỸ THUẬT (B1 - B6)
# ══════════════════════════════════════════════════════════════════════════════

class SKUIntegrityMetric(BaseMetric):
    """Độ đo DeepEval kiểm tra bước B2: Không để trống mã SKU, không chứa tiền tố UNKNOWN."""
    def __init__(self, threshold: float = 1.0):
        super().__init__()
        self.threshold = threshold
        self.score = 0.0
        self.reason = ""
        self.evaluation_model = "deterministic-rule"

    def measure(self, test_case: LLMTestCase) -> float:
        try:
            data = json.loads(test_case.actual_output)
            sku = str(data.get("sku") or "").strip()
            if not sku:
                self.score = 0.0
                self.reason = "Thất bại: Mã SKU bị để trống."
            elif sku.upper().startswith("UNKNOWN"):
                self.score = 0.0
                self.reason = f"Thất bại: Mã SKU chứa tiền tố không xác định '{sku}'."
            else:
                self.score = 1.0
                self.reason = f"Đạt: Mã SKU '{sku}' hợp lệ và định danh duy nhất."
        except Exception as e:
            self.score = 0.0
            self.reason = f"Lỗi phân tích JSON kết quả: {e}"

        self.success = self.score >= self.threshold
        return self.score

    def is_successful(self) -> bool:
        return self.success


class BilingualTitleMetric(BaseMetric):
    """Độ đo DeepEval kiểm tra bước B4: Tiêu đề song ngữ hoàn chỉnh Anh - Việt."""
    def __init__(self, threshold: float = 1.0):
        super().__init__()
        self.threshold = threshold
        self.score = 0.0
        self.reason = ""
        self.evaluation_model = "deterministic-rule"

    def measure(self, test_case: LLMTestCase) -> float:
        try:
            data = json.loads(test_case.actual_output)
            name_vi = str(data.get("product_name") or "").strip()
            name_en = str(data.get("product_name_en") or "").strip()

            if not name_vi or not name_en:
                self.score = 0.0
                self.reason = f"Thất bại: Thiếu tiêu đề song ngữ (VI: '{name_vi}', EN: '{name_en}')."
            elif name_vi.lower() == name_en.lower() and len(name_vi) > 10:
                # Nếu tiêu đề tiếng Việt giống hệt tiếng Anh mà chưa dịch
                self.score = 0.5
                self.reason = "Cảnh báo: Tiêu đề tiếng Việt chưa được bản địa hóa so với tiếng Anh."
            else:
                self.score = 1.0
                self.reason = "Đạt: Đủ cặp tiêu đề chuẩn hóa song ngữ Anh - Việt."
        except Exception as e:
            self.score = 0.0
            self.reason = f"Lỗi phân tích JSON kết quả: {e}"

        self.success = self.score >= self.threshold
        return self.score

    def is_successful(self) -> bool:
        return self.success


class EvidenceQuoteMetric(BaseMetric):
    """Độ đo DeepEval kiểm tra bước B3: Trích dẫn nguyên văn bằng chứng gốc (evidence_quote)."""
    def __init__(self, threshold: float = 1.0):
        super().__init__()
        self.threshold = threshold
        self.score = 0.0
        self.reason = ""
        self.evaluation_model = "deterministic-rule"

    def measure(self, test_case: LLMTestCase) -> float:
        try:
            data = json.loads(test_case.actual_output)
            quote = str(data.get("evidence_quote") or "").strip()

            if not quote or len(quote) < 10:
                self.score = 0.0
                self.reason = "Thất bại: Thiếu trích dẫn nguyên văn bằng chứng gốc hoặc trích dẫn quá ngắn."
            else:
                self.score = 1.0
                self.reason = f"Đạt: Trích dẫn bằng chứng hợp lệ ({len(quote)} ký tự): '{quote[:50]}...'"
        except Exception as e:
            self.score = 0.0
            self.reason = f"Lỗi phân tích JSON: {e}"

        self.success = self.score >= self.threshold
        return self.score

    def is_successful(self) -> bool:
        return self.success


class Haravan7BlockHTMLMetric(BaseMetric):
    """Độ đo DeepEval kiểm tra bước B6: Cấu trúc mô tả sản phẩm chuẩn 7 khối Haravan."""
    def __init__(self, threshold: float = 1.0):
        super().__init__()
        self.threshold = threshold
        self.score = 0.0
        self.reason = ""
        self.evaluation_model = "deterministic-rule"

    def measure(self, test_case: LLMTestCase) -> float:
        try:
            data = json.loads(test_case.actual_output)
            html = str(data.get("html") or data.get("custom_html") or "")
            sku = str(data.get("sku") or "")

            checks = [
                ("Thẻ container bis-product-card", "bis-product-card" in html),
                ("Khối 1: Tiêu đề tiếng Việt", "<h1" in html),
                ("Khối 2: Tiêu đề tiếng Anh", "<h2" in html),
                ("Khối 3: Hãng / Vai trò / Xuất xứ", "Tổ chức / Hãng:" in html or "Đơn vị phân phối:" in html),
                ("Khối 4: Giới thiệu mô tả", "Giới thiệu sản phẩm" in html or "Mô tả" in html or "line-height" in html),
                ("Khối 5: Đặc điểm nổi bật", "<li" in html),
                ("Khối 6 & 7: Phạm vi áp dụng & Liên kết", "Phạm vi áp dụng" in html or "Tra cứu" in html or "https://" in html),
            ]

            failed = [name for name, passed in checks if not passed]
            # Kiểm tra từ cấm
            has_forbidden_word = "chính ngạch" in html.lower()

            if failed:
                self.score = max(0.0, 1.0 - (len(failed) * 0.2))
                self.reason = f"Thất bại: Thiếu các khối Haravan: {', '.join(failed)}"
            elif has_forbidden_word:
                self.score = 0.7
                self.reason = "Cảnh báo: HTML còn chứa từ ngữ bị cấm ('chính ngạch')."
            else:
                self.score = 1.0
                self.reason = "Đạt: Cấu trúc HTML 7 khối hoàn chỉnh, chuẩn quy cách Haravan & BIS Textile."
        except Exception as e:
            self.score = 0.0
            self.reason = f"Lỗi phân tích HTML: {e}"

        self.success = self.score >= self.threshold
        return self.score

    def is_successful(self) -> bool:
        return self.success


# ══════════════════════════════════════════════════════════════════════════════
# 2. CÁC TEST CASES KIỂM THỬ TỰ ĐỘNG (PYTEST + DEEPEVAL)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def technical_agent():
    """Khởi tạo instance AgentTechnical để chạy thẩm định."""
    return AgentTechnical()


def test_aatcc_hardbound_book_full_pipeline(technical_agent):
    """
    Test Case 1: Thẩm định sản phẩm chuẩn AATCC Manual (SKU 03026A).
    Kỳ vọng: Vượt qua cả 4 độ đo (SKU, Song ngữ, Bằng chứng, 7 Khối HTML).
    """
    mock_record = {
        "sku": "03026A",
        "product_name": "Sổ tay Phương pháp Thử nghiệm Tiêu chuẩn Quốc tế AATCC - Bản bìa cứng",
        "product_name_en": "AATCC Manual of International Test Methods and Procedures - Hardbound Book",
        "category": "Tài liệu tiêu chuẩn dệt may",
        "brand": "AATCC (Hoa Kỳ)",
        "brand_evidence": "American Association of Textile Chemists and Colorists (AATCC), Research Triangle Park, NC, USA",
        "description": "Sổ tay kỹ thuật chứa đựng đầy đủ các phương pháp kiểm nghiệm độ bền màu, độ co rút, tính năng kháng nước và quản lý độ ẩm dệt may.",
        "evidence_quote": "AATCC 03026A Manual of International Test Methods and Procedures - Hardbound Book containing all standard test methods.",
        "source_page": "7"
    }

    # Sinh HTML 7 khối
    html_output = technical_agent.build_7_block_html(mock_record)
    mock_record["html"] = html_output

    # Thực hiện 6-Step Audit Pipeline
    audit_res = technical_agent.audit_6_steps(mock_record)

    test_case = LLMTestCase(
        input="Thẩm định kỹ thuật sản phẩm AATCC 03026A từ Catalogue trang 7",
        actual_output=json.dumps(mock_record, ensure_ascii=False)
    )

    # 1. Kiểm tra SKU
    m_sku = SKUIntegrityMetric()
    m_sku.measure(test_case)
    assert m_sku.is_successful(), m_sku.reason

    # 2. Kiểm tra Song ngữ
    m_bilingual = BilingualTitleMetric()
    m_bilingual.measure(test_case)
    assert m_bilingual.is_successful(), m_bilingual.reason

    # 3. Kiểm tra Trích dẫn bằng chứng
    m_quote = EvidenceQuoteMetric()
    m_quote.measure(test_case)
    assert m_quote.is_successful(), m_quote.reason

    # 4. Kiểm tra HTML 7 khối
    m_html = Haravan7BlockHTMLMetric()
    m_html.measure(test_case)
    assert m_html.is_successful(), m_html.reason

    # 5. Kiểm tra kết quả tổng hợp của AgentTechnical
    assert audit_res["overall_pass"] is True, f"Audit 6 bước thất bại: {audit_res}"


def test_reject_empty_or_unknown_sku(technical_agent):
    """
    Test Case 2: Kiểm thử cơ chế từ chối khi SKU rỗng hoặc UNKNOWN.
    Kỳ vọng: SKUIntegrityMetric đánh giá fail (score = 0.0) và B2 không pass.
    """
    bad_record = {
        "sku": "UNKNOWN-9a8b7c",
        "product_name": "Thiết bị thử nghiệm",
        "product_name_en": "Testing Equipment",
        "evidence_quote": "Extracted without SKU from page 12",
        "source_page": "12"
    }

    test_case = LLMTestCase(
        input="Thẩm định sản phẩm thiếu SKU",
        actual_output=json.dumps(bad_record, ensure_ascii=False)
    )

    m_sku = SKUIntegrityMetric()
    m_sku.measure(test_case)
    assert not m_sku.is_successful(), "Hệ thống phải từ chối SKU chứa tiền tố UNKNOWN!"

    audit_res = technical_agent.audit_6_steps(bad_record)
    assert audit_res["b2"]["pass"] is False, "Bước B2 phải trả về False đối với UNKNOWN SKU!"


def test_reject_missing_evidence_quote(technical_agent):
    """
    Test Case 3: Kiểm thử cơ chế chống ảo giác (Anti-hallucination).
    Kỳ vọng: Nếu không có trích dẫn bằng chứng (evidence_quote), hệ thống từ chối duyệt.
    """
    no_quote_record = {
        "sku": "AATCC-TEST-01",
        "product_name": "Máy đo độ bền màu",
        "product_name_en": "Crockmeter Fastness Tester",
        "evidence_quote": "",  # Rỗng
        "source_page": "5"
    }

    test_case = LLMTestCase(
        input="Thẩm định sản phẩm không có trích dẫn bằng chứng",
        actual_output=json.dumps(no_quote_record, ensure_ascii=False)
    )

    m_quote = EvidenceQuoteMetric()
    m_quote.measure(test_case)
    assert not m_quote.is_successful(), "Hệ thống phải bắt buộc có evidence_quote từ trang gốc!"

    audit_res = technical_agent.audit_6_steps(no_quote_record)
    assert audit_res["b3"]["pass"] is False, "Bước B3 phải bắt lỗi khi trích dẫn rỗng!"


# ══════════════════════════════════════════════════════════════════════════════
# 3. RUNNER CHẠY TRỰC TIẾP (PYTHON TEST_BIS_AGENTS.PY)
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n══════════════════════════════════════════════════════════════════")
    print("🚀 ĐANG KHỞI CHẠY BỘ KIỂM THỬ DEEPEVAL CHO AGENT_TECHNICAL (B1-B6)")
    print("══════════════════════════════════════════════════════════════════\n")

    agent = AgentTechnical()

    print("▶ [Test 1] Thẩm định quy trình 6 bước cho SKU 03026A (AATCC Manual):")
    test_aatcc_hardbound_book_full_pipeline(agent)
    print("  ✓ PASS: Đủ SKU, Song ngữ, Trích dẫn gốc và cấu trúc HTML 7 khối Haravan.\n")

    print("▶ [Test 2] Kiểm thử cơ chế loại trừ SKU rỗng / UNKNOWN:")
    test_reject_empty_or_unknown_sku(agent)
    print("  ✓ PASS: Hệ thống đã chặn thành công sản phẩm có mã UNKNOWN.\n")

    print("▶ [Test 3] Kiểm thử rào chắn chống ảo giác (Anti-hallucination Evidence):")
    test_reject_missing_evidence_quote(agent)
    print("  ✓ PASS: Hệ thống đã chặn thành công sản phẩm thiếu evidence_quote.\n")

    print("🎉 TẤT CẢ CÁC ĐỘ ĐO VÀ TEST CASE DEEPEVAL ĐÃ VƯỢT QUA 100% THÀNH CÔNG!")
