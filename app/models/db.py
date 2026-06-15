"""v0 data model: a minimal story bible stored as a JSON blob, plus chapters.
Normalized tables (characters, power_system, plot_threads, …) come in v1."""

from __future__ import annotations

from sqlmodel import Field, Session, SQLModel, create_engine

from app.core.config import settings


class Novel(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    premise: str
    title: str | None = None
    # JSON blob: {"world": ..., "power_system": ..., "characters": [...], "outline": [...]}
    bible_json: str = "{}"


class Chapter(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    novel_id: int = Field(foreign_key="novel.id", index=True)
    n: int
    title: str
    body: str


engine = create_engine(settings.database_url, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
