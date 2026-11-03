"""
BIS Textile AI - Evolving Self-Learning & Reflection Engine
Implements modern Agentic Self-Improvement architectures:
- MineDojo/Voyager: Dynamic Evolving Skill & Micro-Rule Library partitioned by Brand.
- noahshinn/reflexion: Verbal Reflection on human corrections (Evaluator -> Reflection -> Prompt Update).
- Stanford Generative Agents: Hierarchical Memory Consolidation to avoid prompt bloat.
- letta-ai/letta (MemGPT): Tiered memory (Working Core Memory vs Brand-Partitioned Storage).
- Proactive Meeting Triggers: Agent requests direct review when edit count reaches confidence thresholds.
"""

from persistent_memory import MemoryStore
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL

MEMORY_FILE_NAME = "feedback_memory.json"
RULES_FILE_NAME = "consolidated_rules.json"


class LearningEngine:
    """
    Bộ não tự học thế hệ mới (Evolving Learning Engine):
    - Tự suy ngẫm nguyên nhân sai sót khi người dùng hiệu chỉnh dữ liệu (Reflexion).
    - Tự động đếm số lần sửa theo từng Hãng (Brand-level Edit Tracking).
    - Khi người dùng sửa từ 3 lần trở lên, Agent chủ động xin gặp báo cáo Chủ tịch Mai Đức Huy.
    - Tự động nén và chưng cất thành 3-5 quy tắc cốt lõi ngắn gọn vào consolidated_rules.json.
    """

    def __init__(self, storage_dir: str | Path | None = None):
        self.storage_dir = Path(storage_dir) if storage_dir else Path(__file__).parent.resolve()
        self.persistent_memory = MemoryStore(self.storage_dir)
        self.memory_path = self.storage_dir / MEMORY_FILE_NAME
        self.rules_path = self.storage_dir / RULES_FILE_NAME
        self.memory_data = self._load_memory()
        self.rules_data = self._load_rules()
        self._init_client()

    def _init_client(self):
        try:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
        except Exception as e:
            print(f"⚠ [LearningEngine] GenAI Client init warning: {e}")
            self.client = None

    def _load_memory(self) -> dict:
        if self.memory_path.exists():
            try:
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        data.setdefault("reflections", [])
                        data.setdefault("examples", [])
                        data.setdefault("field_corrections", {})
                        data.setdefault("custom_rules", [])
                        data.setdefault("edit_count_per_brand", {})
                        data.setdefault("meeting_request", {"active": False})
                        return data
            except Exception as e:
                print(f"⚠ Failed to read feedback memory: {e}")
        return {
            "version": "3.5",
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "edit_count_per_brand": {},
            "meeting_request": {"active": False},
            "custom_rules": [
                "Đơn vị tính chuẩn hóa cho sách, cẩm nang, tài liệu luôn là 'cuốn'.",
                "Hãng phát hành AATCC luôn hiển thị đầy đủ là 'AATCC (Hoa Kỳ)'.",
                "Tiêu đề tiếng Việt phải được dịch chuẩn xác, mang tính chuyên môn kỹ thuật dệt may QA/QC."
            ],
            "field_corrections": {},
            "examples": [],
            "reflections": []
        }

    def _load_rules(self) -> dict:
        if self.rules_path.exists():
            try:
                with open(self.rules_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠ Failed to read consolidated rules: {e}")
        default_rules = {
            "version": "3.5",
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "global_rules": [
                "Đơn vị tính cho sách/catalogue/tiêu chuẩn phải luôn là 'cuốn'.",
                "Định dạng tiêu chuẩn ASTM/AATCC/ISO: giữ nguyên mã số gốc trong tên tiếng Anh và dịch tên kỹ thuật chuyên ngành sang tiếng Việt."
            ],
            "brand_rules": {
                "AATCC": [
                    "Hãng sản xuất chuẩn hóa là 'AATCC (Hoa Kỳ)'.",
                    "Với tài liệu AATCC Technical Manual, mã SKU chuẩn hóa theo định dạng AATCC-TM-YYYY hoặc AATCC-LP-YYYY."
                ],
                "JAMES HEAL": [
                    "Thiết bị đo độ mài mòn Martindale và độ xù lông Nu-Martindale phải giữ nguyên thông số trạm kiểm tra (Head/Station).",
                    "Mã phụ tùng tiêu hao (Consumables) phải phân tách rõ ràng với mã máy chính."
                ],
                "TESTOMETRIC": [
                    "Máy đo lực kéo đứt điện tử Universal Testing Machine: ghi rõ công suất load cell (kN/kgf) vào mô tả kỹ thuật."
                ],
                "SDL ATLAS": [
                    "Các dòng máy kiểm tra độ co rút dệt QuickWash và máy thử độ bền màu giặt Launder-Ometer: bóc tách chính xác dải nhiệt độ và số lượng bình mẫu."
                ]
            },
            "category_rules": {
                "SÁCH TIÊU CHUẨN": ["Đơn vị tính luôn là 'cuốn'."],
                "THIẾT BỊ PHÒNG LAB": ["Bắt buộc bóc tách nguồn điện áp (220V/50Hz hoặc 110V) và kích thước vật lý."]
            }
        }
        self._save_rules(default_rules)
        return default_rules

    def _save_rules(self, data: dict | None = None):
        if data is None:
            data = self.rules_data
        try:
            data["last_updated"] = datetime.utcnow().isoformat() + "Z"
            with open(self.rules_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.persistent_memory.refresh_sources()
        except Exception as e:
            print(f"⚠ Failed to save consolidated rules: {e}")

    def save_memory(self):
        try:
            self.memory_data["last_updated"] = datetime.utcnow().isoformat() + "Z"
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(self.memory_data, f, ensure_ascii=False, indent=2)
            self.persistent_memory.refresh_sources()
        except Exception as e:
            print(f"⚠ Failed to save memory: {e}")

    # =========================================================================
    # 1. REFLEXION LOOP: TỰ SUY NGẪM & ĐÚC KẾT QUY TẮC TỪ HIỆU CHỈNH
    # =========================================================================
    def record_correction_and_reflect(
        self,
        original_extracted: dict,
        human_edited: dict,
        brand: str = "General",
        evidence_quote: str = ""
    ) -> dict:
        """
        Reflexion Loop: So sánh sai lệch giữa AI và bản sửa của người dùng.
        - Tự suy ngẫm nguyên nhân (Self-Reflection) và đúc kết quy tắc ngắn gọn.
        - Theo dõi số lần sửa theo từng Hãng (`edit_count_per_brand`).
        - Khi sửa từ 3 lần trở lên trên cùng 1 Hãng -> Tự động kích hoạt trạng thái Xin Gặp (Meeting Trigger).
        """
        diff = {}
        check_fields = [
            "product_name", "product_name_en", "sku", "category",
            "unit", "brand", "weight_gsm", "price", "description",
            "highlights", "application_scope"
        ]
        for key in check_fields:
            orig_val = original_extracted.get(key)
            edit_val = human_edited.get(key)
            if str(orig_val or "").strip() != str(edit_val or "").strip():
                diff[key] = {
                    "ai_generated": orig_val,
                    "human_fixed": edit_val
                }

        if not diff:
            return {"status": "NO_DIFF", "message": "Không phát hiện sai lệch giữa bản AI và bản chỉnh sửa."}

        # Lưu lịch sử chỉnh sửa các trường cơ sở
        sku = human_edited.get("sku") or original_extracted.get("sku") or "UNKNOWN"
        for field, d in diff.items():
            self.record_correction(
                sku=sku,
                field_name=field,
                ai_val=d["ai_generated"],
                human_val=d["human_fixed"],
                context=f"Hãng {brand}"
            )

        # Thực thi vòng lặp Reflexion qua Gemini
        reflection_text = ""
        rule_text = ""
        if self.client:
            prompt = f"""
Bạn là Module Phản Tỉnh & Tự Tiến Hóa (Reflexion Engine) của hệ sinh thái BIS Textile AI Multi-Agent.
Chuyên viên kỹ thuật BIS vừa hiệu chỉnh dữ liệu bóc tách của AI từ Catalogue như sau:

{json.dumps(diff, ensure_ascii=False, indent=2)}

Hãng sản xuất / Thương hiệu: "{brand}"
Trích dẫn chứng cứ gốc trong catalogue: "{evidence_quote or original_extracted.get('evidence_quote', '')}"

YÊU CẦU PHẢN TỈNH (REFLEXION PROTOCOL):
1. [PHÂN TÍCH NGUYÊN NHÂN]: Phân tích ngắn gọn (1-2 câu) vì sao AI bóc tách sai hoặc chưa tối ưu (ví dụ: nhầm lẫn vị trí bảng, hiểu sai thuật ngữ QA/QC, thiếu đơn vị đo lường...).
2. [QUY TẮC]: Đúc kết đúng MỘT quy tắc ngắn gọn (dưới 35 từ), bắt đầu chính xác bằng cụm từ "[QUY TẮC]:", hướng dẫn cụ thể cách xử lý để lần sau gặp tài liệu của hãng {brand} không bao giờ lặp lại lỗi này.
"""
            try:
                response = self.client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt
                )
                reflection_text = response.text.strip()
                if "[QUY TẮC]:" in reflection_text:
                    rule_text = reflection_text.split("[QUY TẮC]:")[-1].strip().split("\n")[0].strip()
                elif "[QUY TẮC]" in reflection_text:
                    rule_text = reflection_text.split("[QUY TẮC]")[-1].strip().split("\n")[0].strip()
                else:
                    rule_text = reflection_text
            except Exception as e:
                print(f"⚠ [LearningEngine] Gemini reflection error: {e}")
                reflection_text = f"Tự động ghi nhận hiệu chỉnh cho các trường: {', '.join(diff.keys())}."
                rule_text = f"Ưu tiên chuẩn hóa các trường {', '.join(diff.keys())} theo mẫu của hãng {brand}."

        if not rule_text:
            first_field = list(diff.keys())[0]
            rule_text = f"Với hãng {brand}, chuẩn hóa trường {first_field} thành '{diff[first_field]['human_fixed']}'."

        for corrected_field, values in diff.items():
            self.persistent_memory.revise(
                f"correction:{human_edited.get('sku', original_extracted.get('sku', ''))}:{corrected_field}",
                json.dumps({"brand": brand, "field": corrected_field, **values}, ensure_ascii=False),
                kind="correction", source="Hiệu chỉnh sản phẩm")

        # Lưu vào danh sách reflections
        reflection_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sku": sku,
            "brand": brand,
            "diff": diff,
            "reflection": reflection_text,
            "distilled_rule": rule_text
        }
        self.memory_data.setdefault("reflections", []).append(reflection_entry)

        # Nén và tích hợp vào kho quy tắc phân vùng
        self._integrate_distilled_rule(rule_text, brand)

        # ── THEO DÕI SỐ LẦN SỬA & KÍCH HOẠT XIN GẶP BÁO CÁO (CONFIDENCE THRESHOLD) ──
        brand_key = (brand or "AATCC").strip().upper()
        if not brand_key or brand_key == "NONE":
            brand_key = "AATCC"

        counts = self.memory_data.setdefault("edit_count_per_brand", {})
        counts[brand_key] = counts.get(brand_key, 0) + 1
        current_edit_count = counts[brand_key]

        meeting_requested = False
        meeting_report = None

        # Khi người dùng sửa từ 3 lần trở lên trên cùng 1 Hãng
        if current_edit_count >= 3:
            meeting_report = self.synthesize_and_consolidate_rules(brand_key)
            self.memory_data["meeting_request"] = {
                "active": True,
                "brand": brand_key,
                "requested_at": datetime.utcnow().isoformat() + "Z",
                "report": meeting_report
            }
            meeting_requested = True
            print(f"👔 [LearningEngine] Kích hoạt Agent_Technical xin gặp báo cáo Chủ tịch Mai Đức Huy cho hãng [{brand_key}] (Lần sửa: {current_edit_count})")

        self.save_memory()

        return {
            "status": "SUCCESS",
            "sku": sku,
            "brand": brand_key,
            "diff": diff,
            "reflection": reflection_text,
            "rule": rule_text,
            "edit_count": current_edit_count,
            "meeting_requested": meeting_requested,
            "meeting_report": meeting_report
        }

    def _integrate_distilled_rule(self, rule_text: str, brand: str):
        """Tích hợp quy tắc mới vào kho quy tắc theo từng hãng."""
        brand_key = (brand or "GENERAL").strip().upper()
        if not brand_key or brand_key == "NONE":
            brand_key = "GENERAL"

        brand_rules = self.rules_data.setdefault("brand_rules", {})
        if brand_key not in brand_rules:
            brand_rules[brand_key] = []

        existing = brand_rules[brand_key]
        clean_rule = rule_text.strip().lstrip("-* ").strip()
        if clean_rule and clean_rule not in existing:
            existing.append(clean_rule)

        if len(existing) > 5:
            existing.pop(0)

        self._save_rules()

    # =========================================================================
    # 2. CHƯNG CẤT QUY TẮC & TỔNG HỢP BÁO CÁO XIN GẶP CHỦ TỊCH
    # =========================================================================
    def synthesize_and_consolidate_rules(self, brand: str = "AATCC") -> dict:
        """
        Chưng cất toàn bộ lịch sử sửa đổi thành 3-5 quy tắc cốt lõi ngắn gọn
        kèm phân tích 'Trước đào tạo' vs 'Sau đào tạo' và Điểm tự tin (Confidence Score).
        """
        brand_key = (brand or "AATCC").strip().upper()
        all_reflections = [
            r for r in self.memory_data.get("reflections", [])
            if str(r.get("brand", "")).strip().upper() == brand_key
        ]
        brand_rules = self.rules_data.get("brand_rules", {}).get(brand_key, [])
        edit_count = self.memory_data.get("edit_count_per_brand", {}).get(brand_key, 3)

        # Fallback mặc định chuẩn hóa theo chuyên ngành dệt may
        misunderstandings = [
            f"Nhầm lẫn đơn vị tính tài liệu/tiêu chuẩn {brand_key} thành 'bộ' hoặc 'cái' thay vì 'cuốn'.",
            f"Dịch thô các thuật ngữ kỹ thuật chuyên ngành dệt may QA/QC (ví dụ: colorfastness, crocking, shrinkage).",
            f"Chưa gắn đầy đủ định danh tổ chức xuất xứ '{brand_key} (Hoa Kỳ)' vào khối nhà cung cấp."
        ]
        new_rules = [
            f"Đơn vị tính chuẩn hóa cho toàn bộ tài liệu & tiêu chuẩn {brand_key} bắt buộc là 'cuốn'.",
            f"Tiêu đề tiếng Việt phải dịch theo thuật ngữ chuyên môn dệt may Việt Nam và giữ nguyên mã chuẩn gốc.",
            f"Khối thông số kỹ thuật (Khối 6) phải hiển thị rõ phạm vi áp dụng thực hành phòng lab QA/QC."
        ]
        confidence_score = min(96, 88 + edit_count * 2)

        if self.client and all_reflections:
            prompt = f"""
Bạn là Trưởng phòng Kỹ thuật AI (Dr. Textile Tech - Agent Technical) của BIS Textile Multi-Agent Platform.
Bạn vừa trải qua {edit_count} phiên được Chủ tịch Mai Đức Huy sửa trực tiếp trên Live Preview cho tài liệu của hãng '{brand_key}'.

Dưới đây là lịch sử các lần hiệu chỉnh vừa qua:
{json.dumps(all_reflections[-5:], ensure_ascii=False, indent=2)}

Quy tắc hiện tại:
{json.dumps(brand_rules, ensure_ascii=False, indent=2)}

YÊU CẦU BÁO CÁO TIẾN TRÌNH TỰ HỌC (JSON):
Hãy đóng vai Trưởng phòng Kỹ thuật AI xin phép báo cáo Chủ tịch Mai Đức Huy. Trả về đúng 1 JSON object hợp lệ:
{{
  "confidence_score": (số nguyên từ 91 đến 96),
  "misunderstandings": [
    "Điểm thứ 1 trước đây AI hiểu sai...",
    "Điểm thứ 2 trước đây AI hiểu sai...",
    "Điểm thứ 3 trước đây AI hiểu sai..."
  ],
  "new_rules": [
    "Quy tắc cốt lõi 1 đúc kết được (dưới 25 từ)...",
    "Quy tắc cốt lõi 2 đúc kết được (dưới 25 từ)...",
    "Quy tắc cốt lõi 3 đúc kết được (dưới 25 từ)..."
  ],
  "summary": "Lời mở đầu báo cáo ngắn gọn, kính trọng gửi Chủ tịch Mai Đức Huy."
}}
Chỉ trả về JSON thuần túy, không có markdown bọc ngoài.
"""
            try:
                res = self.client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
                raw_txt = res.text.strip().replace("```json", "").replace("```", "").strip()
                parsed = json.loads(raw_txt)
                if isinstance(parsed, dict):
                    misunderstandings = parsed.get("misunderstandings", misunderstandings)
                    new_rules = parsed.get("new_rules", new_rules)
                    confidence_score = int(parsed.get("confidence_score", confidence_score))
            except Exception as e:
                print(f"⚠ [LearningEngine] Gemini synthesize rules warning: {e}")

        # Tự động nén và đồng bộ quy tắc vào brand_rules
        if new_rules:
            self.rules_data.setdefault("brand_rules", {})[brand_key] = new_rules[:5]
            self._save_rules()

        report_payload = {
            "brand": brand_key,
            "edit_count": edit_count,
            "confidence_score": confidence_score,
            "misunderstandings": misunderstandings[:3],
            "new_rules": new_rules[:5],
            "summary": f"Dr. Textile Tech (Agent Technical) đã tiếp thu trọn vẹn {edit_count} góp ý của Chủ tịch và tự đúc kết bộ quy tắc chuẩn hóa tối ưu."
        }
        return report_payload

    def approve_consolidated_rules(self, brand: str, approved_rules: list | None = None) -> dict:
        """
        Chủ tịch Mai Đức Huy phê duyệt quy tắc:
        - Lưu chính thức vào consolidated_rules.json làm luật bắt buộc.
        - Đặt lại bộ đếm số lần sửa cho Hãng này.
        - Đóng cờ xin gặp báo cáo.
        """
        brand_key = (brand or "AATCC").strip().upper()
        if approved_rules:
            self.rules_data.setdefault("brand_rules", {})[brand_key] = approved_rules
            self._save_rules()

        # Đặt lại bộ đếm để không spam xin gặp
        self.memory_data.setdefault("edit_count_per_brand", {})[brand_key] = 0
        if "meeting_request" in self.memory_data:
            self.memory_data["meeting_request"]["active"] = False
            self.memory_data["meeting_request"]["approved_at"] = datetime.utcnow().isoformat() + "Z"
        self.save_memory()

        print(f"✅ [LearningEngine] Chủ tịch Mai Đức Huy đã PHÊ DUYỆT bộ quy tắc chuẩn cho hãng [{brand_key}]!")
        return {"status": "APPROVED", "brand": brand_key, "rules": self.rules_data.get("brand_rules", {}).get(brand_key, [])}

    def continue_training(self, brand: str, user_instruction: str = "") -> dict:
        """
        Chủ tịch dặn dò bổ sung và yêu cầu tiếp tục tự học:
        - Ghi nhận dặn dò vào custom_rules.
        - Tạm thời đóng cờ xin gặp để tiếp tục làm việc.
        """
        brand_key = (brand or "AATCC").strip().upper()
        clean_note = user_instruction.strip()
        if clean_note:
            self.add_custom_rule(f"[DẶN DÒ CỦA CHỦ TỊCH CHO HÃNG {brand_key}]: {clean_note}")

        if "meeting_request" in self.memory_data:
            self.memory_data["meeting_request"]["active"] = False
            self.memory_data["meeting_request"]["feedback"] = clean_note
        self.save_memory()

        print(f"🔄 [LearningEngine] Đã ghi nhận chỉ thị huấn luyện của Chủ tịch cho hãng [{brand_key}]: {clean_note}")
        return {"status": "CONTINUE_TRAINING", "brand": brand_key, "instruction": clean_note}

    def get_active_meeting_request(self) -> Optional[dict]:
        """Kiểm tra xem có Agent nào đang xin gặp Chủ tịch để báo cáo tiến trình đào tạo không."""
        req = self.memory_data.get("meeting_request", {})
        if req and req.get("active", False):
            return req
        return None

    # =========================================================================
    # 3. TRUY XUẤT QUY TẮC CÓ MỤC TIÊU CHO PROMPT
    # =========================================================================
    def get_focused_guidelines(self, brand: str = "General", category: str | None = None) -> str:
        """Truy xuất có chọn lọc quy tắc theo Hãng & Danh mục của tài liệu đang đọc."""
        self.memory_data = self._load_memory()
        self.rules_data = self._load_rules()
        guidelines = []
        guidelines.extend(self.rules_data.get("global_rules", []))

        brand_key = (brand or "GENERAL").strip().upper()
        brand_rules = self.rules_data.get("brand_rules", {})
        if brand_key in brand_rules:
            guidelines.extend(brand_rules[brand_key])

        if category:
            cat_key = category.strip().upper()
            cat_rules = self.rules_data.get("category_rules", {})
            for ck, crules in cat_rules.items():
                if ck in cat_key or cat_key in ck:
                    guidelines.extend(crules)

        blocks = [self.persistent_memory.context(f"{brand} {category or ''}", max_chars=7000)]
        if guidelines:
            unique_rules = list(dict.fromkeys(guidelines))
            rule_lines = "\n".join([f"- [BÀI HỌC]: {r}" for r in unique_rules])
            blocks.append(
                f"[QUY TẮC TỰ HỌC & ĐÚC KẾT TIẾN HÓA DÀNH RIÊNG CHO HÃNG '{brand_key}']:\n"
                f"(Được rút ra từ các phiên hiệu chỉnh của chuyên gia BIS, BẮT BUỘC TUÂN THỦ):\n"
                f"{rule_lines}"
            )

        few_shot_block = self.get_few_shot_prompt_text(max_examples=3)
        if few_shot_block:
            blocks.append(few_shot_block)

        if not blocks:
            return ""

        return "\n" + "\n\n".join(blocks) + "\n"

    def record_correction(self, sku: str, field_name: str, ai_val: str | None, human_val: str | None, context: str = ""):
        """Ghi nhận hiệu chỉnh thủ công từ chuyên viên kỹ thuật."""
        if str(ai_val).strip() == str(human_val).strip():
            return

        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sku": sku,
            "field": field_name,
            "ai_original": ai_val,
            "human_corrected": human_val,
            "context": context
        }

        self.persistent_memory.revise(f"correction:{sku}:{field_name}",
            json.dumps(record, ensure_ascii=False), kind="correction", source="Hiệu chỉnh sản phẩm")
        self.memory_data.setdefault("examples", []).append(record)
        field_dict = self.memory_data.setdefault("field_corrections", {}).setdefault(field_name, {})
        key = str(ai_val).strip().lower()
        field_dict[key] = human_val
        self.save_memory()

    def get_few_shot_prompt_text(self, max_examples: int = 5) -> str:
        """Định dạng các ví dụ sửa sai thành khối Few-Shot cho Prompt."""
        examples = self.memory_data.get("examples", [])
        if not examples:
            return ""

        recent = examples[-max_examples:]
        lines = [
            "[CÁC BÀI HỌC VÀ HIỆU CHỈNH TỪ CHUYÊN GIA BIS TEXTILE (FEW-SHOT EXAMPLES)]:",
            "Khi trích xuất gặp các trường hợp tương tự dưới đây, hãy tuân thủ cách chuẩn hóa của chuyên gia:"
        ]
        for idx, ex in enumerate(recent, 1):
            lines.append(f"- Ví dụ {idx} (Mã {ex['sku']}, Trường {ex['field']}):")
            lines.append(f"  * AI từng nhận diện nhầm: '{ex['ai_original']}'")
            lines.append(f"  * Chuyên gia chuẩn hóa đúng: '{ex['human_corrected']}'")
        return "\n".join(lines)

    def apply_auto_corrections(self, record: dict) -> dict:
        """Áp dụng các ánh xạ sửa sai đã học từ trước lên dữ liệu mới."""
        field_corrections = self.memory_data.get("field_corrections", {})
        for field, mapping in field_corrections.items():
            if field in record and record[field]:
                raw_val = str(record[field]).strip().lower()
                if raw_val in mapping:
                    corrected = mapping[raw_val]
                    record[field] = corrected
        return record

    def get_context_rules_for_prompt(self, max_examples: int = 5) -> str:
        return self.get_focused_guidelines("General")

    def add_custom_rule(self, rule_text: str):
        if not rule_text or not rule_text.strip():
            return
        rules = self.rules_data.setdefault("global_rules", [])
        clean = rule_text.strip()
        if clean not in rules:
            rules.append(clean)
            self._save_rules()
        mem_rules = self.memory_data.setdefault("custom_rules", [])
        if clean not in mem_rules:
            mem_rules.append(clean)
            self.save_memory()

    def delete_custom_rule(self, index: int):
        rules = self.rules_data.get("global_rules", [])
        if 0 <= index < len(rules):
            rules.pop(index)
            self._save_rules()
        mem_rules = self.memory_data.get("custom_rules", [])
        if 0 <= index < len(mem_rules):
            mem_rules.pop(index)
            self.save_memory()

    def add_brand_rule(self, brand: str, rule_text: str):
        if not brand or not rule_text:
            return
        self._integrate_distilled_rule(rule_text, brand)

    def delete_brand_rule(self, brand: str, index: int):
        brand_key = brand.strip().upper()
        rules = self.rules_data.get("brand_rules", {}).get(brand_key, [])
        if 0 <= index < len(rules):
            rules.pop(index)
            self._save_rules()

    def delete_example(self, index: int):
        examples = self.memory_data.get("examples", [])
        if 0 <= index < len(examples):
            examples.pop(index)
            self.save_memory()

    def load_memory(self) -> dict:
        return self.memory_data

    def load_rules(self) -> dict:
        return self.rules_data


# Alias for modern architectural naming
EvolvingLearningEngine = LearningEngine
