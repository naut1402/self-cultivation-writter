"""Hardcoded v0 AI profiles (Vietnamese cultivation genre).

In v1 these move to the DB with CRUD. For now: edit a dict to change a profile's
model/provider or prompt. Model slugs are LiteLLM "<provider>/<model>" strings.
"""

from __future__ import annotations

from typing import Any

# Prose-heavy roles → strongest model; mechanical roles → cheaper model.
# Swap these slugs to change provider — the LLM wrapper handles dispatch:
#   Anthropic:          "anthropic/claude-opus-4-8"
#   OpenAI:             "openai/gpt-4o"
#   OpenRouter:         "openrouter/deepseek/deepseek-chat"
#   OpenAI-compatible:  "openai/<model>"        (+ set OPENAI_BASE_URL + OPENAI_API_KEY)
#   Local Ollama:       "ollama_chat/qwen2.5:14b"  (+ run `ollama serve`)
PROSE_MODEL = "openrouter/deepseek/deepseek-chat"
MECHANICAL_MODEL = "openrouter/deepseek/deepseek-chat"

PROFILES: dict[str, dict[str, Any]] = {
    "worldbuilder": {
        "name": "Worldbuilder",
        "role": "world",
        "model": PROSE_MODEL,
        "params": {},
        "system_prompt": (
            "Bạn là chuyên gia xây dựng thế giới cho tiểu thuyết tiên hiệp/tu tiên Trung Hoa, "
            "viết bằng tiếng Việt. Dựa trên tiền đề được cung cấp, hãy thiết kế bối cảnh thế giới: "
            "các đại lục/tông môn/thế lực chính, không khí thời đại, quy luật tu luyện tổng quát, "
            "và mâu thuẫn cốt lõi của thế giới. "
            "CHỈ trả về JSON hợp lệ với các khóa: "
            '{"the_gioi": str, "boi_canh": str, "the_luc": [{"ten": str, "mo_ta": str}], '
            '"mau_thuan_coi_loi": str}. Không thêm văn bản ngoài JSON.'
        ),
    },
    "power_system": {
        "name": "Power-System Designer",
        "role": "power_system",
        "model": MECHANICAL_MODEL,
        "params": {},
        "system_prompt": (
            "Bạn là người thiết kế hệ thống tu luyện (cảnh giới) cho truyện tiên hiệp, viết bằng tiếng Việt. "
            "Dựa trên bối cảnh thế giới, hãy xây dựng thang cảnh giới rõ ràng từ thấp đến cao, "
            "quy tắc đột phá, và giới hạn sức mạnh để đảm bảo tính nhất quán về sau. "
            "CHỈ trả về JSON hợp lệ với các khóa: "
            '{"canh_gioi": [{"ten": str, "thu_tu": int, "mo_ta": str}], '
            '"quy_tac_dot_pha": str}. Không thêm văn bản ngoài JSON.'
        ),
    },
    "outliner": {
        "name": "Outliner",
        "role": "outline",
        "model": PROSE_MODEL,
        "params": {},
        "system_prompt": (
            "Bạn là biên kịch/người lập đại cương cho truyện tiên hiệp, viết bằng tiếng Việt. "
            "Dựa trên bối cảnh thế giới và hệ thống cảnh giới, hãy lập đại cương cho 3 chương đầu: "
            "mỗi chương có tiêu đề, mục tiêu, các nhịp sự kiện chính, và 'hook' cuối chương. "
            "Đảm bảo logic leo thang hợp lý theo phong cách tu tiên. "
            "CHỈ trả về JSON hợp lệ: "
            '{"nhan_vat_chinh": {"ten": str, "xuat_than": str, "canh_gioi_dau": str}, '
            '"chuong": [{"so": int, "tieu_de": str, "muc_tieu": str, '
            '"nhip_su_kien": [str], "hook": str}]}. Không thêm văn bản ngoài JSON.'
        ),
    },
    "drafter": {
        "name": "Chapter Drafter",
        "role": "draft",
        "model": PROSE_MODEL,
        "params": {},
        "system_prompt": (
            "Bạn là tiểu thuyết gia tiên hiệp, văn phong tiếng Việt mượt mà, giàu hình ảnh, "
            "đúng chất truyện tu tiên (convert đọc xuôi, không sượng). "
            "Viết trọn vẹn MỘT chương dựa trên: bối cảnh thế giới, hệ thống cảnh giới, đại cương chương, "
            "và tóm tắt chương trước (nếu có). Giữ nhất quán tên riêng và cảnh giới nhân vật. "
            "Độ dài khoảng 1200–1800 từ. Trả về văn xuôi thuần (không JSON, không tiêu đề lặp lại)."
        ),
    },
}
