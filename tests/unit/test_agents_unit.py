import types
from agents.content_improver import ContentImproverAgent
from agents.metadata_recommender import MetadataRecommenderAgent
from agents.repo_analyzer import RepoAnalyzerAgent


def test_content_improver_agent_basic():
    class FakeWeb:
        def search_similar_repos(self, readme, top_k=3):
            return [{"title": "A", "snippet": "s"}]

        def summarize_and_improve(self, readme, examples, style, goal):
            return "# Improved\nBody"

    class FakeRag:
        def retrieve(self, text):
            return ["Suggestion 1"]

    agent = ContentImproverAgent(web_search=FakeWeb(), rag=FakeRag())
    res = agent.run("# Title", {}, style="S", goal="G")
    assert hasattr(res, 'improved_readme')
    assert 'Improved' in res.improved_readme
    assert 'architecture_diagram' in res.suggested_images


def test_metadata_recommender_basic():
    class FakeKeywordExtractor:
        def extract(self, text):
            return ['ai', 'tool', 'demo']

    agent = MetadataRecommenderAgent(FakeKeywordExtractor())
    rec = agent.run('Some README text', {})
    assert isinstance(rec.title_suggestions, list)
    assert isinstance(rec.tags, list)
    assert 'ai' in rec.tags
    assert 'software' in rec.short_description or isinstance(
        rec.short_description, str)


def test_repo_analyzer_basic():
    class FakeParser:
        def parse(self, src):
            return {
                'files': {'a.py': 'print(1)\n', 'README.md': '# Head\nIntro'},
                'README.md': '# Head\nIntro',
                'title': 'T'
            }

    agent = RepoAnalyzerAgent('src', FakeParser())
    analysis = agent.run()
    assert analysis.files
    assert analysis.readme.startswith('# Head')
    assert 'file_count' in analysis.code_stats
    assert isinstance(analysis.missing_sections, list)
