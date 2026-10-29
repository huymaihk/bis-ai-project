"""
BIS Textile AI - Self Learning Engine & Continuous Memory
Records corrections made by operators and injects few-shot examples into future extraction prompts.
"""
import os
import json
from pathlib import Path
from datetime import datetime

MEMORY_FILE_NAME = "feedback_memory.json"

class LearningEngine:
    def __init__(self, storage_dir: str | Path | None = None):
        self.storage_dir = Path(storage_dir) if storage_dir else Path(__file__).parent.resolve()
        self.memory_path = self.storage_dir / MEMORY_FILE_NAME
        self.memory_data = self._load_memory()

    def _load_memory(self) -> dict:
        if self.memory_path.exists():
            try:
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠ Failed to read feedback memory: {e}")
        return {
            "version": "1.0",
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "field_corrections": {},
            "examples": []
        }

    def save_memory(self):
        try:
            self.memory_data["last_updated"] = datetime.utcnow().isoformat() + "Z"
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(self.memory_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠ Failed to save memory: {e}")

    def record_correction(self, sku: str, field_name: str, ai_val: str | None, human_val: str | None, context: str = ""):
        """
        Record a human correction {ai_value -> human_corrected_value}.
        Avoid duplicates and maintain few-shot learning history.
        """
        if str(ai_val).strip() == str(human_val).strip():
            return  # No change

        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sku": sku,
            "field": field_name,
            "ai_original": ai_val,
            "human_corrected": human_val,
            "context": context
        }

        # Save to examples list
        self.memory_data.setdefault("examples", []).append(record)

        # Update specific field corrections dictionary
        field_dict = self.memory_data.setdefault("field_corrections", {}).setdefault(field_name, {})
        key = str(ai_val).strip().lower()
        field_dict[key] = human_val

        self.save_memory()
        print(f"🧠 [LearningEngine] Learned correction for '{field_name}': '{ai_val}' ➔ '{human_val}'")

    def get_few_shot_prompt_text(self, max_examples: int = 5) -> str:
        """
        Format recent corrections into a few-shot instruction block for Gemini prompt.
        """
        examples = self.memory_data.get("examples", [])
        if not examples:
            return ""

        recent = examples[-max_examples:]
        lines = [
            "\n[CÁC BÀI HỌC VÀ HIỆU CHỈNH TỪ CHUYÊN GIA BIS TEXTILE (FEW-SHOT EXAMPLES)]:",
            "Khi trích xuất gặp các trường hợp tương tự dưới đây, hãy tuân thủ cách chuẩn hóa của chuyên gia:"
        ]
        for idx, ex in enumerate(recent, 1):
            lines.append(f"- Ví dụ {idx} (Mã {ex['sku']}, Trường {ex['field']}):")
            lines.append(f"  * AI từng nhận diện nhầm: '{ex['ai_original']}'")
            lines.append(f"  * Chuyên gia chuẩn hóa đúng: '{ex['human_corrected']}'")
        lines.append("--------------------------------------------------------------------------------\n")
        return "\n".join(lines)

    def apply_auto_corrections(self, record: dict) -> dict:
        """
        Automatically correct extracted record based on historical memory before presenting to user.
        """
        field_corrections = self.memory_data.get("field_corrections", {})
        for field, mapping in field_corrections.items():
            if field in record and record[field]:
                raw_val = str(record[field]).strip().lower()
                if raw_val in mapping:
                    corrected = mapping[raw_val]
                    print(f"⚡ [LearningEngine] Auto-corrected {field}: '{record[field]}' ➔ '{corrected}'")
                    record[field] = corrected
        return record

