"""v0 Streamlit page: enter a premise -> generate -> read bible + 3 chapters."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow `import app.*` when run via `streamlit run ui/app.py` from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from app.models.db import Chapter, Novel, get_session, init_db  # noqa: E402
from app.orchestrator.pipeline import generate_novel  # noqa: E402
from sqlmodel import select  # noqa: E402

st.set_page_config(page_title="Tu Tiên Writer (v0)", layout="wide")
st.title("📜 Tu Tiên Writer — v0 prototype")

init_db()

premise = st.text_area(
    "Tiền đề (premise)",
    placeholder="VD: Một thiếu niên phế linh căn nhặt được tàn hồn của một Đại Đế thượng cổ…",
    height=120,
)

if st.button("✨ Tạo truyện", type="primary", disabled=not premise.strip()):
    with st.status("Đang sáng tác…", expanded=True) as status:
        def progress(stage: str, detail: str) -> None:
            status.write(f"**{stage}** — {detail}")

        try:
            novel_id = generate_novel(premise.strip(), progress=progress)
            status.update(label="Hoàn tất!", state="complete")
            st.session_state["novel_id"] = novel_id
        except Exception as exc:  # surface the failure instead of a blank page
            status.update(label="Lỗi", state="error")
            st.exception(exc)

novel_id = st.session_state.get("novel_id")
if novel_id:
    with get_session() as session:
        novel = session.get(Novel, novel_id)
        chapters = session.exec(
            select(Chapter).where(Chapter.novel_id == novel_id).order_by(Chapter.n)
        ).all()

    if novel:
        bible = json.loads(novel.bible_json or "{}")
        col_bible, col_chapters = st.columns([1, 2])
        with col_bible:
            st.subheader("📖 Story bible")
            st.json(bible)
        with col_chapters:
            st.subheader("📝 Chương")
            for ch in chapters:
                with st.expander(f"Chương {ch.n}: {ch.title}", expanded=ch.n == 1):
                    st.write(ch.body)
