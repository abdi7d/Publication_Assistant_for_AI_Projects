import os
import types
import app as app_module
import tools.list_available_models as lam


def test_validate_repo_logic_success(monkeypatch):
    class FakeParser:
        def parse(self, url):
            return {'files': {'a.txt': 'x'}}

    monkeypatch.setattr(app_module, 'RepoParser', FakeParser)
    msg, tree = app_module.validate_repo_logic('https://repo')
    assert 'validated' in msg.lower() or 'success' in msg.lower()
    assert '📄' in tree


def test_generate_full_article_pipeline_exception(monkeypatch):
    class BadOrch:
        def run_pipeline(self, agents, repo_url, style=None, goal=None):
            raise RuntimeError('boom')

    monkeypatch.setattr(app_module, 'Orchestrator', lambda: BadOrch())
    title, sub, tags, body = app_module.generate_full_article(
        'https://x', 'S', 'M', 'm', 'g', 'd')
    assert title == 'Error' or 'Pipeline failed' in body


def test_on_generate_use_existing(monkeypatch):
    # Simulate existing projects
    monkeypatch.setattr(app_module, 'load_projects', lambda: {
                        'exist': {'repo_url': 'https://ex'}})
    # Mock generate_full_article
    monkeypatch.setattr(app_module, 'generate_full_article',
                        lambda *a, **k: ("# Title", "", "<div></div>", "Body"))
    # Call on_generate with Use Existing Project
    out = app_module.on_generate(
        '', 'S', 'M', 'm', 'g', 'd', 'Use Existing Project', 'exist', '')
    # Should return tuple with visibility and title etc
    assert isinstance(out, tuple)


def test_summarize_and_improve_empty_gemini(monkeypatch):
    from tools.web_search import WebSearchTool
    tool = WebSearchTool(selected_model='m', provider='google')

    class MockModels:
        def generate_content(self, model, contents):
            return types.SimpleNamespace(text='')

    class MockClient:
        def __init__(self):
            self.models = MockModels()

    tool.gemini_client = MockClient()
    tool.active_client = tool.gemini_client
    res = tool.summarize_and_improve('# R', [], style='S', goal='G')
    assert 'Error: AI generated an empty response.' in res or 'Error' in res


def test_websearch_no_valid_provider():
    from tools.web_search import WebSearchTool
    tool = WebSearchTool(selected_model='m', provider='none')
    # Provide an active client without models or chat
    tool.active_client = types.SimpleNamespace()
    tool.gemini_client = None
    tool.groq_client = None
    out = tool.summarize_and_improve('# R', [], style='S', goal='G')
    assert 'No valid LLM provider' in out or 'Error: No valid LLM provider' in out


def test_list_gemini_models_print(monkeypatch, capsys):
    class FakeModel:
        def __init__(self, name):
            self.name = name

    class FakeClient:
        def __init__(self, api_key=None):
            pass

        class models:
            @staticmethod
            def list():
                return [FakeModel('m1'), FakeModel('m2')]

    monkeypatch.setenv('GOOGLE_API_KEY', 'token')
    monkeypatch.setattr(lam, 'genai', types.SimpleNamespace(Client=FakeClient))
    lam.list_gemini_models()
    out = capsys.readouterr().out
    assert 'Available models' in out or 'm1' in out
