"""v0 sequential writing pipeline (no state machine, no n8n).

premise -> world -> power_system -> outline -> draft ch.1-3, persisting a
JSON-blob story bible and the chapters to SQLite.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any

from app.llm.client import LLMClient
from app.models.db import Chapter, Novel, get_session, init_db
from app.profiles.seed import PROFILES

Progress = Callable[[str, str], None]
N_CHAPTERS = 3


def _noop(_stage: str, _detail: str) -> None:
    pass


def _parse_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from a model response, tolerating code fences."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
    return json.loads(text)


def generate_novel(
    premise: str,
    *,
    client: LLMClient | None = None,
    progress: Progress | None = None,
) -> int:
    client = client or LLMClient()
    progress = progress or _noop
    init_db()

    # 1. World
    progress("world", "Đang dựng thế giới…")
    world = _parse_json(client.run_profile(PROFILES["worldbuilder"], premise, json_mode=True))

    # 2. Power system
    progress("power_system", "Đang thiết kế hệ thống cảnh giới…")
    power = _parse_json(
        client.run_profile(
            PROFILES["power_system"],
            f"Bối cảnh thế giới:\n{json.dumps(world, ensure_ascii=False)}",
            json_mode=True,
        )
    )

    # 3. Outline (incl. protagonist + 3 chapters)
    progress("outline", "Đang lập đại cương 3 chương…")
    outline = _parse_json(
        client.run_profile(
            PROFILES["outliner"],
            "Bối cảnh:\n"
            f"{json.dumps(world, ensure_ascii=False)}\n\n"
            "Hệ thống cảnh giới:\n"
            f"{json.dumps(power, ensure_ascii=False)}",
            json_mode=True,
        )
    )

    bible = {"world": world, "power_system": power, "outline": outline}

    with get_session() as session:
        novel = Novel(
            premise=premise,
            title=world.get("the_gioi"),
            bible_json=json.dumps(bible, ensure_ascii=False),
        )
        session.add(novel)
        session.commit()
        session.refresh(novel)
        novel_id = novel.id
        assert novel_id is not None

        # 4. Draft chapters 1..N
        prev_summary = ""
        chapters = outline.get("chuong", [])[:N_CHAPTERS]
        for ch in chapters:
            num = ch.get("so")
            progress("draft", f"Đang viết chương {num}…")
            context = (
                f"BỐI CẢNH:\n{json.dumps(world, ensure_ascii=False)}\n\n"
                f"HỆ THỐNG CẢNH GIỚI:\n{json.dumps(power, ensure_ascii=False)}\n\n"
                f"NHÂN VẬT CHÍNH:\n{json.dumps(outline.get('nhan_vat_chinh', {}), ensure_ascii=False)}\n\n"
                f"ĐẠI CƯƠNG CHƯƠNG NÀY:\n{json.dumps(ch, ensure_ascii=False)}\n\n"
                f"TÓM TẮT CHƯƠNG TRƯỚC:\n{prev_summary or '(chưa có)'}"
            )
            body = client.run_profile(PROFILES["drafter"], context)
            session.add(
                Chapter(novel_id=novel_id, n=num, title=ch.get("tieu_de", f"Chương {num}"), body=body)
            )
            session.commit()
            prev_summary = body[-1200:]

    progress("done", "Hoàn tất.")
    return novel_id
