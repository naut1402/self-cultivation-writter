# Self-Cultivation Writer

AI agents that write Chinese cultivation (xianxia / *tu tiên*) novels **in Vietnamese**.

- **Backend writing "skills":** [n8n](https://n8n.io) flows exposed over **MCP** (planned, v1).
- **App:** Python — FastAPI core + Streamlit UI (MCP client), owning the orchestration loop, story bible, and AI-profile registry.
- **LLM:** provider-agnostic via [LiteLLM](https://github.com/BerriAI/litellm) — Claude / OpenAI / OpenRouter / DeepSeek, switchable per profile.

See the full architecture, roadmap (v0→v3), and issue backlog in the plan file referenced by the team.

## v0 — local prototype

Pure-Python vertical slice: **premise → world → power-system → outline → 3 chapters**, persisted to SQLite, read in Streamlit. No n8n, no cloud.

### Run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   *nix: source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env        # then add an LLM key (e.g. ANTHROPIC_API_KEY)

pytest                      # provider param-sanitizing tests (no network)
streamlit run ui/app.py     # open the UI, enter a premise, generate
```

### Layout

```
app/
  core/          # config / settings
  llm/           # LLMClient over LiteLLM (provider dispatch + param sanitizing)
  models/        # SQLModel tables (v0: novels + chapters, bible as JSON blob)
  profiles/      # hardcoded VN AI profiles (worldbuilder, power-system, outliner, drafter)
  orchestrator/  # sequential v0 pipeline
ui/              # Streamlit app
n8n/             # placeholder for v1 n8n flow exports (empty in v0)
  flows/
tests/
```

Switch model/provider per role by editing the slugs in `app/profiles/seed.py`
(e.g. `anthropic/claude-opus-4-8`, `openai/gpt-4o`, `openrouter/deepseek/deepseek-chat`).
