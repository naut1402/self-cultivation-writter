"""Smoke test: app package and submodules import without error (AC for #1)."""


def test_app_submodules_importable():
    import app.core.config
    import app.llm.client
    import app.models.db
    import app.orchestrator.pipeline
    import app.profiles.seed

    assert app.core.config.settings is not None
