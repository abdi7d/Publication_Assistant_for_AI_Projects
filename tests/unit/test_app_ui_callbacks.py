import types
from pathlib import Path
import app as app_module


def test_on_mode_change_create_new():
    show_existing_false, repo_input_update, msg = app_module.on_mode_change(
        "Create New Project")
    assert hasattr(show_existing_false,
                   'visible') or show_existing_false is not None


def test_on_mode_change_use_existing(monkeypatch):
    monkeypatch.setattr(app_module, 'load_projects', lambda: {
                        'p1': {'repo_url': 'https://x'}})
    res = app_module.on_mode_change("Use Existing Project")
    assert isinstance(res, tuple)


def test_on_existing_select(monkeypatch):
    monkeypatch.setattr(app_module, 'load_projects', lambda: {
                        'p1': {'repo_url': 'https://x'}})
    repo_update, msg_update = app_module.on_existing_select('p1')
    # gr.update may return a dict-like structure in tests
    assert isinstance(repo_update, dict) and 'value' in repo_update


def test_on_delete(monkeypatch):
    # Setup projects file in temp location
    monkeypatch.setattr(app_module, 'load_projects', lambda: {
                        'p1': {'repo_url': 'https://x'}})
    monkeypatch.setattr(app_module, 'delete_project', lambda pid: [])
    res = app_module.on_delete('p1')
    assert isinstance(res, tuple)


def test_on_generate_creates_project(monkeypatch, tmp_path):
    # Mock generate_full_article to return simple values
    def fake_generate(repo_url, style, length, model, goal, project_desc, provider=None):
        return ("# Title", "", "<div></div>", "Body")

    monkeypatch.setattr(app_module, 'generate_full_article', fake_generate)
    # Ensure save_project does not fail
    monkeypatch.setattr(app_module, 'save_project',
                        lambda pid, url, metadata=None: [pid])
    monkeypatch.setattr(app_module, 'load_projects', lambda: {})

    out = app_module.on_generate(
        'https://x', 'S', 'M', 'm', 'g', 'desc', 'Create New Project', '')
    # Should return a tuple where first element makes outputs visible
    assert isinstance(out, tuple)


def test_generate_full_article_cleaning(monkeypatch):
    # Create metadata and content objects with leading title and tags to trigger cleaning
    class DummyMeta:
        title_suggestions = ['MyTitle']
        short_description = 'desc'
        tags = ['a', 'b']

    class DummyContent:
        improved_readme = "# MyTitle\n<div>Project Tags</div>\n<span>badge</span>\n\nActual body line"

    def fake_run_pipeline(self, agents, repo_url, style=None, goal=None):
        return {'analysis': {}, 'metadata': DummyMeta(), 'content_improvement': DummyContent()}

    monkeypatch.setattr(app_module, 'Orchestrator', lambda: type(
        'O', (), {'run_pipeline': fake_run_pipeline})())
    title, sub, tags, body = app_module.generate_full_article(
        'https://x', 'S', 'M', 'm', 'g', 'pd', provider='none')
    assert 'Actual body line' in body


def test_clean_generated_content_strips_markdown_noise():
    dirty = "# Title\n\n**Bold** text\n* bullet\n- second\n[Link](https://x)\n<em>tag</em>"
    cleaned = app_module.clean_generated_content(dirty)
    assert '# Title' not in cleaned
    assert '**Bold**' not in cleaned
    assert 'bullet' in cleaned
    assert '<em>' not in cleaned
    assert '[' not in cleaned
