import asyncio
import json
import logging
import random

from openai import (
    APIError as OpenAIAPIError,
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)

from src.core.config import settings
from src.core.exceptions import LLMServiceError
from src.apps.tender.schemas import TenderSummaryResponse

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = "Ты — помощник для извлечения информации из тендерной документации."


class LLMService:
    """Сервис для взаимодействия с языковыми моделями."""

    def __init__(self) -> None:
        self.client = AsyncOpenAI(**settings.openai_client_args)

    async def summarize_tender(self, raw_text: str) -> TenderSummaryResponse:
        """
        Отправляет текст в OpenAI и возвращает структурированную выжимку по тендеру.

        Args:
            raw_text: Извлеченный текст из PDF.

        Returns:
            Объект TenderSummaryResponse с выжимкой.

        Raises:
            LLMServiceError: При ошибках обращения к API или невалидном ответе.
        """
        prompt = self._build_prompt(self._truncate_text(raw_text))

        last_error: Exception | None = None
        for attempt in range(1, settings.openai_max_retries + 1):
            try:
                raw_response = await self._request_completion(prompt)
                return self._parse_response(raw_response)
            except (RateLimitError, APIConnectionError, APITimeoutError, LLMServiceError) as exc:
                last_error = exc
                logger.warning(
                    "Попытка %d/%d обращения к LLM не удалась: %s",
                    attempt,
                    settings.openai_max_retries,
                    exc,
                )
                if attempt < settings.openai_max_retries:
                    await asyncio.sleep(self._backoff(attempt))

        raise LLMServiceError(
            f"Не удалось получить корректный ответ от LLM после "
            f"{settings.openai_max_retries} попыток: {last_error}"
        ) from last_error

    async def _request_completion(self, prompt: str) -> str:
        """Выполняет один запрос к LLM и возвращает сырой текст ответа."""
        logger.debug("Запрос к LLM, модель=%s", settings.openai_model)
        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=settings.openai_temperature,
                response_format={"type": "json_object"},
            )
        except OpenAIAPIError as exc:
            logger.error("Ошибка OpenAI API: %s", exc)
            raise LLMServiceError(f"Ошибка при обращении к LLM: {exc}") from exc

        content = response.choices[0].message.content or ""
        logger.debug("Ответ LLM получен, длина=%d", len(content))
        return content

    def _build_prompt(self, text: str) -> str:
        """Строит промпт для LLM."""
        return f"""
Проанализируй следующий текст тендерной документации и верни ответ строго в формате JSON.

Требуемые поля:
- contract_amount: сумма контракта в рублях (число), если не найдено — null.
- deadline: срок выполнения (строка), если не найден — null.
- requirements: список ключевых требований к исполнителю (массив строк).
- penalties: список штрафных санкций (массив строк).

Текст документации:
---
{text}
---

Ответ предоставь строго в формате JSON.
"""

    def _parse_response(self, raw_response: str) -> TenderSummaryResponse:
        """Парсит ответ от LLM в структурированный объект."""
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            logger.error("LLM вернул невалидный JSON: %s", exc)
            raise LLMServiceError("Получен невалидный JSON от LLM.") from exc

        try:
            return TenderSummaryResponse(
                contract_amount=data.get("contract_amount"),
                deadline=data.get("deadline"),
                requirements=data.get("requirements", []),
                penalties=data.get("penalties", []),
                raw_text_preview=raw_response[:200],
            )
        except Exception as exc:
            logger.error("Не удалось разобрать ответ LLM: %s", exc)
            raise LLMServiceError(f"Не удалось разобрать ответ LLM: {exc}") from exc

    @staticmethod
    def _truncate_text(raw_text: str) -> str:
        """Обрезает текст до допустимой длины, логируя факт обрезки."""
        if len(raw_text) <= settings.max_text_length:
            return raw_text
        logger.warning(
            "Текст обрезан с %d до %d символов",
            len(raw_text),
            settings.max_text_length,
        )
        return raw_text[: settings.max_text_length]

    @staticmethod
    def _backoff(attempt: int) -> float:
        """Экспоненциальная задержка с небольшим джиттером."""
        base = settings.openai_retry_backoff * (2 ** (attempt - 1))
        return base + random.uniform(0, 0.5)
