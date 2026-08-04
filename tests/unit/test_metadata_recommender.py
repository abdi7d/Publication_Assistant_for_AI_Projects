from agents.metadata_recommender import MetadataRecommenderAgent
from unittest.mock import patch, MagicMock
import sys
import os


def test_metadata_recommender_heuristic(mock_keyword_extractor):
    agent = MetadataRecommenderAgent(keyword_extractor=mock_keyword_extractor)
    rec = agent.run(readme_text="Short readme about AI and ML.", code_files={})

    assert len(rec.tags) >= 1
    assert isinstance(rec.title_suggestions, list)
    assert isinstance(rec.short_description, str)


def test_metadata_recommender_genai_client_init_fails(mock_keyword_extractor):
    """Test when genai.Client() raises exception (lines 35-36 coverage)"""
    with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}, clear=False):
        with patch('agents.metadata_recommender.genai') as mock_genai:
            # Make genai not None but Client() fails
            mock_genai.Client.side_effect = Exception("API Error")

            agent = MetadataRecommenderAgent(
                keyword_extractor=mock_keyword_extractor)
            assert agent.model is None

            # Should work with fallback
            rec = agent.run(readme_text="AI project", code_files={})
            assert isinstance(rec.short_description, str)


def test_metadata_recommender_no_api_key(mock_keyword_extractor):
    """Test when no API key is provided (lines 33-34 coverage)"""
    with patch.dict(os.environ, {}, clear=True):
        agent = MetadataRecommenderAgent(
            keyword_extractor=mock_keyword_extractor)
        # Should use fallback when no API key
        rec = agent.run(readme_text="AI project", code_files={})

        assert isinstance(rec.title_suggestions, list)
        assert isinstance(rec.short_description, str)


def test_metadata_recommender_no_keywords(mock_keyword_extractor):
    """Test with empty keywords (edge case)"""
    mock_kw = MagicMock()
    mock_kw.extract.return_value = []

    agent = MetadataRecommenderAgent(keyword_extractor=mock_kw)
    rec = agent.run(readme_text="Some readme", code_files={})

    assert isinstance(rec.title_suggestions, list)
    assert isinstance(rec.short_description, str)


def test_metadata_recommender_uses_repo_files_for_tags(mock_keyword_extractor):
    mock_kw = MagicMock()
    mock_kw.extract.return_value = ["ai", "ml"]

    agent = MetadataRecommenderAgent(keyword_extractor=mock_kw)
    rec = agent.run(
        readme_text="A Python project for building an AI assistant.",
        code_files={
            "app.py": "import fastapi",
            "requirements.txt": "fastapi\nuvicorn",
        },
    )

    assert any(tag.lower() in {"python", "fastapi", "uvicorn"}
               for tag in rec.tags)
    assert rec.short_description
