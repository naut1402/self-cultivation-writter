# Cấu trúc dự án — Self-Cultivation Writer

> Rule tham chiếu cấu trúc repo cho agent. Phiên bản hiện tại: **v0** (prototype Python local).
> Kiến trúc đầy đủ (n8n/MCP, Postgres, FastAPI, deploy) **chưa có trong code** — xem roadmap v1→v3.

## Tổng quan

Ứng dụng AI viết tiểu thuyết tiên hiệp/tu tiên Trung Hoa **bằng tiếng Việt**. v0 là vertical slice thuần Python:

**premise → world → power_system → outline → draft 3 chương** → lưu SQLite → đọc qua Streamlit.

| Thành phần | Công nghệ v0 | Ghi chú |
|---|---|---|
| Runtime | Python ≥ 3.11 | Dùng `.venv/Scripts/python.exe` trên Windows |
| LLM | LiteLLM | Provider-agnostic; đổi slug trong `app/profiles/seed.py` |
| DB | SQLite (`scw.db`) | SQLModel; bible = JSON blob |
| UI | Streamlit | `ui/app.py` |
| Test | pytest + ruff | Không gọi network trong test LLM params |

## Cây thư mục

```
self-cultivation-writter/
├── CLAUDE.md                 # Hướng dẫn chính cho agent (commands, kiến trúc, provider)
├── README.md                 # Giới thiệu + hướng dẫn chạy nhanh
├── pyproject.toml            # Package metadata, deps, ruff, pytest config
├── .env.example              # Template biến môi trường (copy → .env)
├── .gitignore
│
├── app/                      # Package Python chính (wheel target)
│   ├── __init__.py
│   ├── core/
│   │   └── config.py         # Settings từ .env; mirror API keys → os.environ cho LiteLLM
│   ├── llm/
│   │   └── client.py         # LLMClient — chokepoint provider quirks (sanitize_params, resolve_api_base)
│   ├── models/
│   │   └── db.py             # SQLModel: Novel, Chapter; engine SQLite; init_db / get_session
│   ├── profiles/
│   │   └── seed.py           # AI profiles hardcoded (worldbuilder, power_system, outliner, drafter)
│   └── orchestrator/
│       └── pipeline.py       # generate_novel() — pipeline tuần tự v0
│
├── ui/
│   └── app.py                # Streamlit: nhập premise → generate → xem bible + chương
│
├── n8n/                      # Placeholder v1 — export JSON n8n flows (trống ở v0)
│   ├── README.md
│   └── flows/                # .gitkeep — export từ n8n UI sau này
│
├── tests/
│   ├── test_imports.py       # Smoke import app.* (AC #1)
│   └── test_llm_params.py      # Test sanitize_params / resolve_api_base (không network)
│
└── .claude/
    ├── settings.local.json   # Cấu hình Claude Code local
    └── rules/                # Rule files cho agent (coding, PR, cấu trúc, …)
        ├── project-structure.md   # (file này)
        ├── coding-rules.md
        ├── commit-message.md
        ├── create-pr.md
        ├── memory/           # Rule liên quan task memory / investigation
        └── …
```

**Không commit:** `.env`, `.venv/`, `*.db`, `__pycache__/`, `.pytest_cache/`

**Runtime tạo ra:** `scw.db` (SQLite local, gitignored)

## Luồng dữ liệu v0

```
ui/app.py
    │  premise + nút "Tạo truyện"
    ▼
app/orchestrator/pipeline.py :: generate_novel()
    │
    ├─► app/profiles/seed.py :: PROFILES["worldbuilder"]     → JSON world
    ├─► PROFILES["power_system"]                             → JSON power_system
    ├─► PROFILES["outliner"]                                 → JSON outline (+ nhan_vat_chinh, chuong[])
    ├─► Lưu Novel (bible_json blob) vào SQLite
    └─► PROFILES["drafter"] × 3 chương                       → Chapter rows
            │
            ▼
    app/llm/client.py :: LLMClient.run_profile() / complete()
            │
            ▼
    LiteLLM → provider (Anthropic / OpenRouter / OpenAI-compat / Ollama)
```

Mỗi bước bible gọi LLM với `json_mode=True`; `_parse_json()` trong pipeline chịu trách nhiệm parse JSON lenient (bỏ code fence, trích `{...}` ngoài cùng).

Mỗi chương draft nhận context: world + power_system + nhan_vat_chinh + đại cương chương + tóm tắt 1200 ký tự cuối chương trước.

## Module chi tiết

### `app/core/config.py`

- `Settings` (pydantic-settings): `database_url`, API keys, `openai_base_url`, `ollama_base_url`
- Default DB: `sqlite:///./scw.db`
- Mirror keys vào `os.environ` để LiteLLM đọc được

### `app/llm/client.py`

**Điểm duy nhất xử lý đặc thù provider.** Orchestrator và profiles không biết provider cụ thể.

| Hàm / class | Vai trò |
|---|---|
| `sanitize_params()` | Bỏ `temperature`/`top_p`/`top_k`/`budget_tokens` cho Claude 4.x; thêm adaptive thinking |
| `resolve_api_base()` | `ollama_chat/*` → Ollama local; `openai/*` → `OPENAI_BASE_URL` nếu có |
| `LLMClient.complete()` | Gọi `litellm.completion` |
| `LLMClient.run_profile()` | Dispatch profile dict từ seed |

### `app/profiles/seed.py`

- `PROSE_MODEL` / `MECHANICAL_MODEL` — đổi **hai slug này** để đổi provider toàn cục
- `PROFILES` — 4 profile: `worldbuilder`, `power_system`, `outliner`, `drafter`
- Mỗi profile: `{name, role, model, params, system_prompt}` — prompt **tiếng Việt**
- v1: chuyển sang DB + CRUD (chưa có)

### `app/orchestrator/pipeline.py`

- `generate_novel(premise, *, client, progress) -> int` — trả `novel_id`
- `N_CHAPTERS = 3`
- `progress(stage, detail)` — callback cho UI (Streamlit status)
- Không state machine, không n8n

### `app/models/db.py`

| Bảng | Cột chính | Ghi chú |
|---|---|---|
| `Novel` | `premise`, `title`, `bible_json` | `bible_json` keys: `world`, `power_system`, `outline` |
| `Chapter` | `novel_id`, `n`, `title`, `body` | FK → `novel.id` |

Schema chuẩn hóa (characters, plot_threads, timeline, …) là **v1** — không tìm các bảng đó trong v0.

### `ui/app.py`

- Entry UI: `streamlit run ui/app.py` từ repo root
- `sys.path` inject để `import app.*` hoạt động
- Hiển thị bible JSON + expander từng chương

### `tests/test_llm_params.py`

- Chỉ test logic param sanitizing và api_base resolution
- Không mock/gọi LLM thật

## Nơi thêm code mới (v0)

| Muốn làm gì | Đặt ở đâu |
|---|---|
| Thêm/sửa AI profile hoặc đổi model | `app/profiles/seed.py` |
| Sửa quy tắc provider (Claude 400, Ollama base, …) | `app/llm/client.py` |
| Thêm bước pipeline (vd. review, rewrite) | `app/orchestrator/pipeline.py` |
| Thêm bảng / field DB | `app/models/db.py` |
| Biến môi trường mới | `app/core/config.py` + `.env.example` |
| UI Streamlit | `ui/app.py` (hoặc tách module trong `ui/` nếu phình to) |
| Unit test | `tests/test_*.py` |

**Không tạo** (chưa có trong repo, thuộc roadmap):

- `fastapi/`, `api/`, MCP server, n8n flows
- Postgres migration, Alembic
- Module `characters/`, `plot_threads/` tách riêng (v1)

## Dependencies chính (`pyproject.toml`)

- `litellm` — multi-provider LLM
- `sqlmodel` — ORM + Pydantic models
- `streamlit` — UI
- `pydantic-settings` — config
- Dev: `pytest`, `ruff`

## Commands tham chiếu nhanh

```bash
# Cài đặt
.venv/Scripts/python.exe -m pip install -e ".[dev]"

# Test
.venv/Scripts/python.exe -m pytest -q

# Chạy UI
.venv/Scripts/python.exe -m streamlit run ui/app.py
```

Trên Windows, set `PYTHONUTF8=1` khi in tiếng Việt ra stdout.

## Liên kết tài liệu khác

- `CLAUDE.md` — commands, provider slugs, git/repo notes
- `.claude/rules/coding-rules.md` — quy tắc code chung
- `.claude/rules/database-schema-guide.md` — schema (khi có / v1)
- GitHub issues nhãn `release:v0` … `release:v3` — backlog theo release
