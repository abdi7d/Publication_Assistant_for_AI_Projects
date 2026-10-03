import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

import app as app_module
from tools.repo_parser import RepoParser
from tools.rag_retriever import RAGRetriever
from tools.web_search import WebSearchTool
from utils.publication_builder import PublicationBuilder


def test_api_projects_history_saved_settings_and_help(client, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(app_module, 'PROJECTS_FILE', tmp_path / 'projects.json')
    monkeypatch.setattr(app_module, 'HISTORY_FILE', tmp_path / 'history.json')
    monkeypatch.setattr(app_module, 'SAVED_FILE', tmp_path / 'saved.json')
    monkeypatch.setattr(app_module, 'UPLOADS_DIR', tmp_path / 'uploads')

    res = client.post('/api/projects', json={
        'project_id': 'p1',
        'repo_url': 'https://example.com/repo',
        'metadata': {'title': 'Demo'},
    })
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert 'p1' in data['projects']

    res = client.get('/api/projects')
    assert res.status_code == 200
    assert 'p1' in res.json()

    res = client.post('/api/history', json={'entry': {'repo': 'https://example.com/repo', 'timestamp': 'now'}})
    assert res.status_code == 200
    history = res.json()
    assert 'entries' in history

    res = client.get('/api/history')
    assert res.status_code == 200
    assert isinstance(res.json(), dict)

    res = client.post('/api/saved', json={'item': {'id': '1', 'name': 'demo'}})
    assert res.status_code == 200
    saved = res.json()
    assert 'items' in saved

    res = client.get('/api/saved')
    assert res.status_code == 200
    assert isinstance(res.json(), dict)

    res = client.delete('/api/saved', json={'key': '1'})
    assert res.status_code == 200
    assert isinstance(res.json(), dict)

    res = client.get('/api/settings')
    assert res.status_code == 200
    assert res.json() == {}

    res = client.post('/api/settings', json={'data': {'foo': 'bar'}})
    assert res.status_code == 200
    assert res.json()['ok'] is True
    assert res.json()['settings']['foo'] == 'bar'

    res = client.get('/api/help')
    assert res.status_code == 200
    assert 'docs_url' in res.json()
    assert 'contact' in res.json()

    res = client.get('/api/analytics')
    assert res.status_code == 200
    analytics = res.json()
    assert analytics['projects_count'] >= 0
    assert 'generation_count' in analytics


def test_api_upload_file_and_invalid_extension(client, monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, 'UPLOADS_DIR', tmp_path / 'uploads')
    (tmp_path / 'uploads').mkdir()

    res = client.post(
        '/api/upload',
        files=[('files', ('test.txt', b'hello', 'text/plain'))],
    )
    assert res.status_code == 200
    assert res.json()['saved'][0]['filename'] == 'test.txt'

    res = client.post(
        '/api/upload',
        files=[('files', ('bad.exe', b'hello', 'application/octet-stream'))],
    )
    assert res.status_code == 400
    assert 'error' in res.json()


def test_api_generate_error_path(monkeypatch, client):
    monkeypatch.setattr(app_module, '_run_generation_with_timeout', lambda *args, **kwargs: (None, 'timeout'))
    payload = {
        'repo_url': 'https://example.com/repo',
        'style': 'Technical Blog',
        'length': 'Medium',
        'model': app_module.DEFAULT_MODEL_NAME,
        'goal': '',
        'project_desc': '',
    }
    res = client.post('/api/generate', json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body['status'] == 'error'
    assert 'error' in body


def test_api_generate_async_and_status_and_result(monkeypatch, client, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(app_module, 'generate_full_article', lambda *args, **kwargs: ('# Title', 'Subtitle', '<div></div>', 'Body'))

    class FakeThread:
        def __init__(self, target, daemon):
            self._target = target

        def start(self):
            self._target()

    monkeypatch.setattr(app_module.threading, 'Thread', FakeThread)

    payload = {
        'repo_url': 'https://example.com/repo',
        'style': 'Technical Blog',
        'length': 'Medium',
        'model': app_module.DEFAULT_MODEL_NAME,
        'goal': '',
        'project_desc': '',
    }
    res = client.post('/api/generate_async', json=payload)
    assert res.status_code == 200
    job_id = res.json()['job_id']
    assert job_id

    status_res = client.get(f'/api/generate_status?job_id={job_id}')
    assert status_res.status_code == 200
    status_json = status_res.json()
    assert status_json['id'] == job_id
    assert status_json['state'] in {'RUNNING', 'SUCCESS', 'ERROR', 'CANCELLED'}

    result_res = client.get(f'/api/generate_result?job_id={job_id}')
    assert result_res.status_code in {200, 202}


def test_api_generate_status_and_cancel_not_found(client):
    res = client.get('/api/generate_status?job_id=missing')
    assert res.status_code == 404

    res = client.post('/api/generate_cancel', json={})
    assert res.status_code == 400
    assert res.json()['error'] == 'missing job_id'

    res = client.post('/api/generate_cancel', json={'job_id': 'missing'})
    assert res.status_code == 200
    assert res.json()['ok'] is False

    res = client.get('/api/generate_result?job_id=missing')
    assert res.status_code == 404


def test_static_pages_available(client):
    for path in ['/index.html', '/analytics.html', '/results.html', '/projects.html', '/saved.html', '/help.html', '/history.html', '/generate.html', '/settings.html']:
        res = client.get(path)
        assert res.status_code == 200
        assert res.headers['content-type'].startswith('text/html')


def test_job_manager_basic_flow():
    jm = app_module.JobManager()
    job_id = jm.create_job({'repo_url': 'x'})
    assert jm.get(job_id)['state'] == 'IDLE'
    jm.start(job_id, ['A', 'B'])
    assert jm.get(job_id)['state'] == 'RUNNING'
    jm.update_step(job_id, 'A', 'IN_PROGRESS', 'work')
    jm.set_state(job_id, 'SUCCESS')
    assert jm.get(job_id)['state'] == 'SUCCESS'
    jm.set_result(job_id, {'title': 'T'})
    assert jm.get(job_id)['result']['title'] == 'T'
    jm.set_error(job_id, 'oops')
    assert jm.get(job_id)['state'] == 'ERROR'
    assert jm.cancel(job_id) is True
    assert jm.get('missing') is None


def test_repo_parser_invalid_and_file_url(tmp_path):
    parser = RepoParser()
    result = parser.parse('not-a-valid-url')
    assert isinstance(result, dict)

    # file:// local path branch
    repo_dir = tmp_path / 'repo'
    repo_dir.mkdir()
    (repo_dir / 'README.md').write_text('# Repo')
    result = parser.parse(f'file://{repo_dir}')
    assert result['files']
    assert 'README.md' in result['files']


def test_rag_retriever_ensure_list_floats_various_inputs():
    assert RAGRetriever._ensure_list_floats([1, 2, 3]) == [1.0, 2.0, 3.0]
    assert RAGRetriever._ensure_list_floats((1, 2, 3)) == [1.0, 2.0, 3.0]
    assert RAGRetriever._ensure_list_floats({'embedding': [1, 2]}) == [1.0, 2.0]
    assert RAGRetriever._ensure_list_floats({'values': [3, 4]}) == [3.0, 4.0]
    assert RAGRetriever._ensure_list_floats({'embeddings': [5, 6]}) == [5.0, 6.0]
    class E:
        def __init__(self):
            self.embedding = [7, 8]
    assert RAGRetriever._ensure_list_floats(E()) == [7.0, 8.0]
    class V:
        def __init__(self):
            self.values = [9, 10]
    assert RAGRetriever._ensure_list_floats(V()) == [9.0, 10.0]
    assert RAGRetriever._ensure_list_floats('invalid') is None


def test_publication_builder_inference_and_markdown_processing():
    builder = PublicationBuilder()
    assert builder._slugify_id('Hello World!') == 'hello-world'
    assert builder._slugify_id('<b>Test</b>') == 'test'
    tree = builder._render_tree({})
    assert 'repository/' in tree

    files = {
        'ui/app.py': 'import fastapi\n',
        'Dockerfile': 'FROM python:3.11',
        'README.md': '# Demo',
        'image.png': 'binary',
    }
    tech_stack = builder._infer_tech_stack(files)
    assert any(name == 'FastAPI' or name == 'Docker' for name, _ in tech_stack)
    evidence = builder._infer_repo_evidence({'app.py': '@app.get("/health")', 'Dockerfile': ''})
    assert '/health' in evidence['endpoints']
    cli_flags = builder._infer_cli_flags({'main.py': 'parser.add_argument("--repo-path")'})
    assert '--repo-path' in cli_flags
    env_vars = builder._infer_env_vars({'app.py': 'GOOGLE_API_KEY'})
    assert 'GOOGLE_API_KEY' in env_vars
    images = builder._detect_images({'logo.png': ''})
    assert 'logo.png' in images

    md = "## Table of Contents\n\n[TOC]\n\n## README Review\n\n### Missing or Weak Areas\n\nA\n\n### Recommendations\n\nB\n\n![Alt](image.png)\n\n```graph\nflow\n```\n"
    processed = builder._post_process_markdown(md)
    assert '## Table of Contents' in processed
    assert '## README Review' in processed
    assert '<figure>' in processed
    assert '```mermaid' in processed


def test_web_search_search_similar_repos_error_branches(monkeypatch):
    tool = WebSearchTool()

    class FakeSearch:
        def invoke(self, query):
            return 'not-a-list'

    tool.search = FakeSearch()
    assert tool.search_similar_repos('q') == []

    class FakeSearch2:
        def invoke(self, query):
            return [1, {'title': 'Repo', 'url': 'https://x', 'content': 'desc'}]

    tool.search = FakeSearch2()
    out = tool.search_similar_repos('q', top_k=2)
    assert isinstance(out, list)
    assert out[0]['title'] == 'Repo'
