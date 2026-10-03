from pathlib import Path
import types
import sys
import asyncio
import json
import os
import tempfile
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from importlib import util
from pathlib import Path

compat_path = Path(__file__).resolve().parent / "compat_testclient.py"
spec = util.spec_from_file_location("compat_testclient", compat_path)
compat_testclient = util.module_from_spec(spec)
spec.loader.exec_module(compat_testclient)
CompatTestClient = compat_testclient.CompatTestClient


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_client():
    # Import the real FastAPI app from app.py
    from app import app as real_app
    client = CompatTestClient(real_app)
    yield client


@pytest.fixture
def client():
    # Import the real FastAPI app from app.py
    from app import app as real_app
    client = CompatTestClient(real_app)
    return client


@pytest.fixture(scope="session")
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    try:
        import shutil

        shutil.rmtree(d)
    except Exception:
        pass


@pytest.fixture
def sample_prompt():
    return "Summarize the following paper: Title: Example"


@pytest.fixture
def tmp_repo(tmp_path):
    # Create a small repository layout for tests
    repo = tmp_path / "sample_repo"
    repo.mkdir()
    readme = repo / "README.md"
    readme.write_text(
        "# Sample Project\n\nThis is a sample README for tests.\n\nUsage: run.sh")
    (repo / "run.py").write_text("print('hello')")
    return str(repo)


@pytest.fixture
def sample_parsed(tmp_path):
    files = {"README.md": "# T\n\nShort description.",
             "src/app.py": "print('x')"}
    return {"files": files, "README.md": files["README.md"], "title": "T"}


@pytest.fixture
def mock_repo_parser(sample_parsed):
    class P:
        def parse(self, src):
            return sample_parsed

    return P()


@pytest.fixture
def mock_keyword_extractor():
    class K:
        def extract(self, text):
            return ["ai", "ml", "pytorch"]

    return K()


@pytest.fixture
def mock_web_search():
    class W:
        def search_similar_repos(self, readme, top_k=3):
            return [{"title": "Example1", "snippet": "An example snippet."}]

        def summarize_and_improve(self, context_readme, examples, style="", goal=""):
            # Return a deterministic improved README
            return "# Improved Title\n\nImproved content based on RAG hints and examples."

    return W()


@pytest.fixture
def mock_rag():
    class R:
        def retrieve(self, text):
            return ["Add installation instructions.", "Add usage examples."]

    return R()


@pytest.fixture
def mock_scholar():
    class S:
        def search(self, query, max_results=1):
            # Simple heuristic: if query contains 'novel' return a hit
            if "novel" in query.lower():
                return [{"title": "Paper on Novel Method"}]
            return []

    return S()


def _inject_fake_langgraph():
    """Inject a tiny fake `langgraph.graph` module into sys.modules.
    This provides a mini StateGraph compatible API used by Orchestrator tests.
    """

    mod = types.ModuleType("langgraph.graph")

    class StateGraph:
        def __init__(self, t):
            self._nodes = {}
            self._edges = {}
            self._entry = None

        def add_node(self, name, fn):
            self._nodes[name] = fn

        def set_entry_point(self, name):
            self._entry = name

        def add_edge(self, a, b):
            self._edges.setdefault(a, []).append(b)

        def compile(self):
            nodes = self._nodes
            edges = self._edges

            class Compiled:
                def __init__(self, entry, nodes, edges):
                    self.entry = entry
                    self.nodes = nodes
                    self.edges = edges

                def invoke(self, inputs):
                    state = dict(inputs)
                    cur = self.entry
                    # Run nodes following the first outgoing edge until END
                    while cur is not None:
                        fn = self.nodes.get(cur)
                        if fn is None:
                            break
                        out = fn(state)
                        if isinstance(out, dict):
                            state.update(out)
                        # Move to next node (first edge) or end
                        nxts = self.edges.get(cur, [])
                        if not nxts:
                            cur = None
                        else:
                            # Follow first edge for determinism
                            cur = nxts[0]
                    return state

            return Compiled(self._entry, nodes, edges)

    setattr(mod, "StateGraph", StateGraph)
    setattr(mod, "END", object())
    sys.modules["langgraph.graph"] = mod


@pytest.fixture
def fake_langgraph():
    # Provide the module for the duration of a test
    _inject_fake_langgraph()
    yield
    # cleanup
    sys.modules.pop("langgraph.graph", None)


# Ensure project root is on sys.path so tests can import top-level packages
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
