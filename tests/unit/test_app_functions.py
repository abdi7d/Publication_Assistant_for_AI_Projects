import os
import json
import tempfile
from pathlib import Path

import pytest

import app as app_module


def test_slugify_and_render_tags():
    assert app_module.slugify('My Repo!') == 'my-repo'
    assert app_module.slugify('') == 'project'
    html = app_module.render_tags_as_html(['one', 'two'])
    assert 'one' in html and 'two' in html


def test_projects_load_save_delete(tmp_path, monkeypatch):
    temp_file = tmp_path / "proj.json"
    monkeypatch.setattr(app_module, 'PROJECTS_FILE', Path(temp_file))

    # ensure empty at start
    assert app_module.load_projects() == {}

    keys = app_module.save_project('p1', 'https://x', {'a': 1})
    assert 'p1' in keys
    loaded = app_module.load_projects()
    assert loaded['p1']['repo_url'] == 'https://x'

    remaining = app_module.delete_project('p1')
    assert 'p1' not in remaining


def test_validate_repo_logic_fallback(monkeypatch, tmp_path):
    # Monkeypatch RepoParser to raise on remote parse and succeed on local
    class FakeParser:
        def parse(self, url):
            if url.startswith('http'):
                raise RuntimeError('remote fail')
            return {'files': {'README.md': 'content'}}

    monkeypatch.setattr(app_module, 'RepoParser', FakeParser)

    # Should use fallback and return a message containing 'offline'
    msg, tree = app_module.validate_repo_logic('https://example.com/repo')
    assert 'offline' in msg.lower(
    ) or 'using offline' in msg.lower() or 'fallback' in msg.lower()
    assert 'README.md' in tree


def test_generate_full_article_simple(monkeypatch, tmp_path):
    # Prevent actual orchestration; mock Orchestrator.run_pipeline
    class DummyMeta:
        title_suggestions = ['T']
        short_description = 'desc'
        tags = ['a']

    class DummyContent:
        improved_readme = '# T\nContent body'

    def fake_run_pipeline(self, agents, repo_url, style=None, goal=None):
        return {'analysis': {}, 'metadata': DummyMeta(), 'content_improvement': DummyContent()}

    monkeypatch.setattr(app_module, 'Orchestrator', lambda: type(
        'O', (), {'run_pipeline': fake_run_pipeline})())

    title, sub, tags_html, body = app_module.generate_full_article(
        'https://x', 'S', 'M', 'm', 'g', 'pd', provider='none')
    assert title.startswith('# T')
    assert 'Project Tags' in tags_html
    assert 'Content body' in body
