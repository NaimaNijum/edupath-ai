"""GeminiProvider is embeddings-only (text generation moved to OpenRouter,
see test_llm_openrouter.py). These tests cover embed_text's response
handling."""

from unittest.mock import MagicMock

import pytest

from app.core.exceptions import LLMError
from app.llm.gemini import GeminiProvider


class MockEmbedding:
    def __init__(self, values):
        self.values = values


class MockEmbedResponse:
    def __init__(self, values):
        self.embeddings = [MockEmbedding(values)] if values is not None else []


@pytest.fixture
def mock_gemini_client():
    mock_client = MagicMock()
    provider = GeminiProvider()
    provider._client = mock_client
    return provider, mock_client


def test_embed_text_returns_values(mock_gemini_client):
    provider, mock_client = mock_gemini_client
    mock_client.models.embed_content.return_value = MockEmbedResponse([0.1] * 1536)

    values = provider.embed_text("some text")

    assert len(values) == 1536
    assert values[0] == pytest.approx(0.1)


def test_embed_text_missing_values_raises_llmerror(mock_gemini_client):
    provider, mock_client = mock_gemini_client
    mock_client.models.embed_content.return_value = MockEmbedResponse(None)

    with pytest.raises(LLMError, match="missing values"):
        provider.embed_text("some text")


def test_embed_text_dimension_mismatch_raises_llmerror(mock_gemini_client):
    provider, mock_client = mock_gemini_client
    mock_client.models.embed_content.return_value = MockEmbedResponse([0.1] * 10)  # not 1536

    with pytest.raises(LLMError, match="dimension mismatch"):
        provider.embed_text("some text")
