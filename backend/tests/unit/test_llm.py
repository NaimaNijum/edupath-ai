
import json
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel, Field

from app.core.exceptions import LLMError
from app.llm.gemini import GeminiProvider

class MockGeminiResponse:
    def __init__(self, text, usage_metadata=None):
        self.text = text
        self.usage_metadata = usage_metadata or {"prompt_token_count": 10, "candidates_token_count": 20, "total_token_count": 30}

class SampleModel(BaseModel):
    name: str
    value: int

@pytest.fixture
def mock_gemini_client():
    mock_client = MagicMock()
    provider = GeminiProvider()
    provider._client = mock_client
    return provider, mock_client

def test_generate_structured_with_markdown_fences(mock_gemini_client):
    """Verify that JSON wrapped in markdown code fences is parsed correctly."""
    provider, mock_client = mock_gemini_client
    response_text = '```json\n{"name": "test", "value": 123}\n```'
    mock_client.models.generate_content.return_value = MockGeminiResponse(response_text)

    structured_result, _ = provider.generate_structured("some prompt", response_model=SampleModel)

    assert structured_result.name == "test"
    assert structured_result.value == 123

def test_generate_structured_with_plain_json(mock_gemini_client):
    """Verify that plain JSON is parsed correctly."""
    provider, mock_client = mock_gemini_client
    response_text = '{"name": "test", "value": 123}'
    mock_client.models.generate_content.return_value = MockGeminiResponse(response_text)

    structured_result, _ = provider.generate_structured("some prompt", response_model=SampleModel)

    assert structured_result.name == "test"
    assert structured_result.value == 123
    
def test_generate_structured_empty_response(mock_gemini_client):
    """Verify an empty response raises an LLMError."""
    provider, mock_client = mock_gemini_client
    mock_client.models.generate_content.return_value = MockGeminiResponse("")

    with pytest.raises(LLMError, match="Gemini returned an empty response"):
        provider.generate_structured("some prompt", response_model=SampleModel)

def test_generate_structured_invalid_json(mock_gemini_client):
    """Verify that invalid JSON raises an LLMError."""
    provider, mock_client = mock_gemini_client
    response_text = '{"name": "test", "value": 123,}' # Trailing comma is invalid
    mock_client.models.generate_content.return_value = MockGeminiResponse(response_text)

    with pytest.raises(LLMError, match="Invalid JSON response from Gemini"):
        provider.generate_structured("some prompt", response_model=SampleModel)

def test_generate_structured_validation_error(mock_gemini_client):
    """Verify that a schema mismatch raises a Pydantic validation error."""
    provider, mock_client = mock_gemini_client
    # 'value' must be an integer, but the model receives an array.
    response_text = '{"name": "test", "value": [1, 2, 3]}'
    mock_client.models.generate_content.return_value = MockGeminiResponse(response_text)

    with pytest.raises(LLMError, match="Gemini response failed Pydantic validation"):
        provider.generate_structured("some prompt", response_model=SampleModel)
