import os
import zipfile
import subprocess
import types
import tempfile
from pathlib import Path

import pytest

from tools.repo_parser import RepoParser
from agents.fact_checker import FactCheckerAgent
from agents.reviewer_critic import ReviewerCriticAgent
from agents.metadata_recommender import MetadataRecommenderAgent


def test_parse_dir_and_zip(tmp_path):
    d = tmp_path / 'repo'
    d.mkdir()
    (d / 'README.md').write_text('# Hello\nIntro')
    (d / 'a.py').write_text('print(1)')
    # large file should be skipped
    large = d / 'big.bin'
    large.write_bytes(b'0' * 120_000)

    rp = RepoParser()
    res = rp.parse(str(d))
    assert 'files' in res
    assert 'README.md' in res and res['README.md'].startswith('# Hello')

    # create zip
    zip_path = tmp_path / 'repo.zip'
    with zipfile.ZipFile(str(zip_path), 'w') as z:
        z.writestr('README.md', '# Zipped')
        z.writestr('b.txt', 'data')

    res2 = rp.parse(str(zip_path))
    assert 'README.md' in res2 and res2['README.md'].startswith('# Zipped')


def test_parse_git_clone_failure(monkeypatch):
    rp = RepoParser()

    def fake_check_call(cmd):
        raise subprocess.CalledProcessError(1, cmd)
    monkeypatch.setattr(subprocess, 'check_call', fake_check_call)
    with pytest.raises(RuntimeError):
        rp.parse('https://example.com/repo.git')


def test_fact_checker_agent(monkeypatch):
    class FakeScholar:
        def search(self, q, max_results=1):
            return [{'title': 'Paper A'}]

    agent = FactCheckerAgent(FakeScholar())
    text = 'This is a novel approach that outperforms prior work in experiments and is state-of-the-art in tests.'
    res = agent.run(text)
    assert isinstance(res.claims_found, list)
    assert res.verified or res.flagged


def test_reviewer_critic_agent():
    agent = ReviewerCriticAgent()
    review = agent.run('No installation provided here', {'total_lines': 5})
    assert isinstance(review.score, float)
    assert any('Missing' in i for i in review.issues)


def test_metadata_recommender_with_model(monkeypatch):
    class FakeKeywordExtractor:
        def extract(self, text):
            return ['alpha', 'beta', 'gamma']

    agent = MetadataRecommenderAgent(FakeKeywordExtractor())

    class FakeModels:
        def generate_content(self, model, contents):
            return types.SimpleNamespace(text='Title One, Title Two, Title Three')

    fake_client = types.SimpleNamespace(models=FakeModels())
    agent.model = fake_client

    rec = agent.run('Some README text', {})
    assert isinstance(rec.title_suggestions, list)
    assert len(rec.title_suggestions) >= 1
