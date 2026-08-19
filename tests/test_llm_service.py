from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from openai import APIConnectionError, RateLimitError

from src.apps.tender.services.llm_service import LLMService
from src.core.config import settings
from src.core.exceptions import LLMServiceError


FakeClient = SimpleNamespace
FakeResponse = SimpleNamespace
VALID_JSON = (
    '{"contract_amount": 1500000, "deadline": "30 дней", '
    '"requirements": ["лицензия"], "penalties": ["штраф"]}'
)


def _make_client(create_result=None, create_side_effect=None):
    create = AsyncMock(return_value=create_result, side_effect=create_side_effect)
    return FakeClient(chat=FakeClient(completions=FakeClient(create=create)))


def _make_response(content: str) -> FakeResponse:
    return FakeResponse(choices=[FakeResponse(message=FakeResponse(content=content))])


def _service_with_client(client) -> LLMService:
    with patch("src.apps.tender.services.llm_service.AsyncOpenAI", return_value=client):
        service = LLMService()
    return service


@pytest.mark.asyncio
async def test_summarize_returns_parsed_response():
    service = _service_with_client(_make_client(create_result=_make_response(VALID_JSON)))

    result = await service.summarize_tender("текст тендера")

    assert result.contract_amount == 1500000.0
    assert result.deadline == "30 дней"
    assert result.requirements == ["лицензия"]
    assert result.penalties == ["штраф"]
    assert result.raw_text_preview == VALID_JSON[:200]


@pytest.mark.asyncio
async def test_summarize_raises_on_invalid_json():
    service = _service_with_client(_make_client(create_result=_make_response("not json")))

    with pytest.raises(LLMServiceError, match="невалидный JSON"):
        await service.summarize_tender("текст")


def _rate_limit_error() -> RateLimitError:
    request = httpx.Request("POST", "http://localhost/v1/chat/completions")
    response = httpx.Response(429, request=request)
    return RateLimitError("429", response=response, body=None)


@pytest.mark.asyncio
async def test_summarize_raises_after_all_retries_fail():
    service = _service_with_client(_make_client(create_side_effect=_rate_limit_error()))

    with pytest.raises(LLMServiceError, match="после"):
        await service.summarize_tender("текст")


@pytest.mark.asyncio
async def test_summarize_retries_then_succeeds():
    create = AsyncMock(side_effect=[_rate_limit_error(), _make_response(VALID_JSON)])
    client = FakeClient(chat=FakeClient(completions=FakeClient(create=create)))
    service = _service_with_client(client)

    result = await service.summarize_tender("текст")

    assert create.await_count == 2
    assert result.contract_amount == 1500000.0


@pytest.mark.asyncio
async def test_summarize_wraps_api_error():
    service = _service_with_client(
        _make_client(create_side_effect=APIConnectionError(request=None))
    )

    with pytest.raises(LLMServiceError):
        await service.summarize_tender("текст")


def test_truncate_keeps_short_text():
    text = "x" * 100
    assert LLMService._truncate_text(text) == text


def test_truncate_cuts_long_text():
    text = "x" * (settings.max_text_length + 500)
    result = LLMService._truncate_text(text)
    assert len(result) == settings.max_text_length


def test_backoff_grows_and_adds_jitter():
    first = LLMService._backoff(1)
    second = LLMService._backoff(2)
    assert second >= first
    assert 0 <= first - settings.openai_retry_backoff <= 0.5
