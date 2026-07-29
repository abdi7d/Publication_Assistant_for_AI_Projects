import types
from tools.web_search import WebSearchTool


def test_gemini_failure_no_groq():
    tool = WebSearchTool(selected_model='m', provider='google')

    class BadModels:
        def generate_content(self, model, contents):
            raise RuntimeError('gemini error')

    class BadClient:
        def __init__(self):
            self.models = BadModels()

    tool.gemini_client = BadClient()
    tool.groq_client = None
    tool.active_client = tool.gemini_client

    out = tool.summarize_and_improve('# R', [], style='S', goal='G')
    assert 'Error generating' in out or 'Error' in out


def test_groq_failure_no_gemini():
    tool = WebSearchTool(selected_model='m', provider='groq')

    class BadCompletions:
        def create(self, model, messages):
            raise RuntimeError('groq error')

    class BadChat:
        def __init__(self):
            self.completions = BadCompletions()

    class BadGroqClient:
        def __init__(self):
            self.chat = BadChat()

    tool.groq_client = BadGroqClient()
    tool.gemini_client = None
    tool.active_client = tool.groq_client

    out = tool.summarize_and_improve('# R', [], style='S', goal='G')
    assert 'Error generating' in out or 'Error' in out
