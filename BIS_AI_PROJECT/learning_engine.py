"""
BIS Textile AI - Evolving Self-Learning & Reflection Engine
Implements modern Agentic Self-Improvement architectures:
- MineDojo/Voyager: Dynamic Evolving Skill & Micro-Rule Library partitioned by Brand.
- noahshinn/reflexion: Verbal Reflection on human corrections (Evaluator -> Reflection -> Prompt Update).
- Stanford Generative Agents: Hierarchical Memory Consolidation to avoid prompt bloat.
- letta-ai/letta (MemGPT): Tiered memory (Working Core Memory vs Brand-Partitioned Storage).
"""

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
    - Tự động nén và tổng quát hóa các lỗi lặp lại thành Quy tắc chuẩn (Consolidation).
    - Phân vùng tri thức theo Hãng & Danh mục để nạp chính xác vào prompt của AgentTechnical.
    """

    def __init__(self, storage_dir: str | Path | None = None):
        self.storage_dir = Path(storage_dir) if storage_dir else Path(__file__).parent.resolve()
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
                        return data
            except Exception as e:
                print(f"⚠ Failed to read feedback memory: {e}")
        return {
            "version": "3.0",
            "last_updated": datetime.utcnow().isoformat() + "Z",
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
            "version": "3.0",
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
        except Exception as e:
            print(f"⚠ Failed to save consolidated rules: {e}")

    def save_memory(self):
        try:
            self.memory_data["last_updated"] = datetime.utcnow().isoformat() + "Z"
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(self.memory_data, f, ensure_ascii=False, indent=2)
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
        Gọi Gemini để tự suy ngẫm nguyên nhân (Self-Reflection) và đúc kết quy tắc [QUY TẮC].
        Tự động nén vào consolidated_rules.json theo từng Hãng (Brand-Partitioned Storage).
        """
        diff = {}
        check_fields = [
            "product_name", "product_name_en", "sku", "category",
            "unit", "brand", "weight_gsm", "price", "description"
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

        # Lưu vào danh sách reflections (Working/Archival Memory)
        reflection_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sku": sku,
            "brand": brand,
            "diff": diff,
            "reflection": reflection_text,
            "distilled_rule": rule_text
        }
        self.memory_data.setdefault("reflections", []).append(reflection_entry)
        self.save_memory()

        # Nén và tích hợp vào kho quy tắc phân vùng (Consolidated Rules)
        self._integrate_distilled_rule(rule_text, brand)

        return {
            "status": "SUCCESS",
            "sku": sku,
            "brand": brand,
            "diff": diff,
            "reflection": reflection_text,
            "rule": rule_text
        }

    def _integrate_distilled_rule(self, rule_text: str, brand: str):
        """
        Tích hợp quy tắc mới vào kho quy tắc, tự động giới hạn tối đa 5 quy tắc
        mỗi hãng để ngăn chặn hiện tượng tràn context (theo Generative Agents).
        """
        brand_key = (brand or "GENERAL").strip().upper()
        if not brand_key or brand_key == "NONE":
            brand_key = "GENERAL"

        brand_rules = self.rules_data.setdefault("brand_rules", {})
        if brand_key not in brand_rules:
            brand_rules[brand_key] = []

        # Tránh trùng lặp nội dung
        existing = brand_rules[brand_key]
        clean_rule = rule_text.strip().lstrip("-* ").strip()
        if clean_rule and clean_rule not in existing:
            existing.append(clean_rule)

        # Giữ tối đa 5 quy tắc cốt lõi tinh hoa nhất cho mỗi hãng
        if len(existing) > 5:
            existing.pop(0)

        self._save_rules()
        print(f"🎯 [LearningEngine] Đã nạp quy tắc tiến hóa mới cho [{brand_key}]: {clean_rule}")

    # =========================================================================
    # 2. RETRIEVAL: TRUY XUẤT QUY TẮC CÓ MỤC TIÊU CHO PROMPT AGENT TECHNICAL
    # =========================================================================
    def get_focused_guidelines(self, brand: str = "General", category: str | None = None) -> str:
        """
        Truy xuất có chọn lọc quy tắc theo Hãng & Danh mục của tài liệu đang đọc,
        kèm 3 ví dụ Few-shot gần nhất để nạp trực tiếp vào Prompt của Gemini.
        """
        guidelines = []
        # 1. Quy tắc chung toàn hệ thống
        guidelines.extend(self.rules_data.get("global_rules", []))

        # 2. Quy tắc riêng biệt của Hãng tài liệu (Brand-Specific Micro-Rules)
        brand_key = (brand or "GENERAL").strip().upper()
        brand_rules = self.rules_data.get("brand_rules", {})
        if brand_key in brand_rules:
            guidelines.extend(brand_rules[brand_key])

        # 3. Quy tắc theo danh mục sản phẩm (nếu có)
        if category:
            cat_key = category.strip().upper()
            cat_rules = self.rules_data.get("category_rules", {})
            for ck, crules in cat_rules.items():
                if ck in cat_key or cat_key in ck:
                    guidelines.extend(crules)

        blocks = []
        if guidelines:
            unique_rules = list(dict.fromkeys(guidelines))
            rule_lines = "\n".join([f"- [BÀI HỌC]: {r}" for r in unique_rules])
            blocks.append(
                f"[QUY TẮC TỰ HỌC & ĐÚC KẾT TIẾN HÓA DÀNH RIÊNG CHO HÃNG '{brand_key}']:\n"
                f"(Được rút ra từ các phiên hiệu chỉnh của chuyên gia BIS, BẮT BUỘC TUÂN THỦ):\n"
                f"{rule_lines}"
            )

        # 4. Bổ sung Few-shot examples gần nhất
        few_shot_block = self.get_few_shot_prompt_text(max_examples=3)
        if few_shot_block:
            blocks.append(few_shot_block)

        if not blocks:
            return ""

        return "\n" + "\n\n".join(blocks) + "\n"

    # =========================================================================
    # 3. CONSOLIDATION: NÉN & TỔNG QUÁT HÓA CÁC QUY TẮC (GENERATIVE AGENTS)
    # =========================================================================
    def consolidate_brand_rules(self, brand: str = "General") -> str:
        """
        Tự động nén hàng chục lỗi nhỏ thành 3-5 nguyên lý cốt lõi cấp cao
        nhằm tối ưu hóa số lượng token và tăng độ tổng quát.
        """
        brand_key = (brand or "GENERAL").strip().upper()
        brand_rules = self.rules_data.get("brand_rules", {}).get(brand_key, [])
        if len(brand_rules) < 3 or not self.client:
            return "Chưa đủ số lượng quan sát để chạy nén tri thức."

        prompt = f"""
Bạn là Chuyên gia Tối ưu hóa Bộ nhớ AI của BIS Textile.
Dưới đây là các quy tắc bóc tách kỹ thuật hiện tại của hãng '{brand_key}':
{json.dumps(brand_rules, ensure_ascii=False, indent=2)}

Nhiệm vụ:
Tổng hợp, gộp các quy tắc trùng lặp hoặc cụ thể hóa nhỏ lẻ thành TỐI ĐA 3 quy tắc tổng quát, súc tích (mỗi quy tắc dưới 30 từ), bắt đầu bằng dấu gạch đầu dòng '- '.
"""
        try:
            res = self.client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            lines = [l.strip().lstrip("-* ").strip() for l in res.text.strip().split("\n") if l.strip()]
            valid_rules = [l for l in lines if len(l) > 10][:4]
            if valid_rules:
                self.rules_data.setdefault("brand_rules", {})[brand_key] = valid_rules
                self._save_rules()
                return f"Đã nén thành công {len(valid_rules)} quy tắc tinh hoa cho hãng {brand_key}."
        except Exception as e:
            return f"Lỗi khi nén quy tắc: {e}"
        return "Không có thay đổi sau khi nén."

    # =========================================================================
    # 4. CÁC HÀM TƯƠNG THÍCH NGƯỢC (BACKWARD COMPATIBILITY)
    # =========================================================================
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

        self.memory_data.setdefault("examples", []).append(record)

        field_dict = self.memory_data.setdefault("field_corrections", {}).setdefault(field_name, {})
        key = str(ai_val).strip().lower()
        field_dict[key] = human_val

        self.save_memory()
        print(f"🧠 [LearningEngine] Đã lưu Few-shot cho '{field_name}': '{ai_val}' ➔ '{human_val}'")

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
                    print(f"⚡ [LearningEngine] Tự động sửa trường {field}: '{record[field]}' ➔ '{corrected}'")
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
        # Also sync to memory_data
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
