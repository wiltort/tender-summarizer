from pydantic import BaseModel, Field


class TenderSummaryResponse(BaseModel):
    contract_amount: float | None = Field(None, description="Сумма контракта в рублях")
    deadline: str | None = Field(None, description="Срок выполнения")
    requirements: list[str] = Field(default_factory=list, description="Ключевые требования")
    penalties: list[str] = Field(default_factory=list, description="Список штрафных санкций")
    raw_text_preview: str | None = Field(None, description="Превью исходного текста")


class ErrorResponse(BaseModel):
    detail: str
