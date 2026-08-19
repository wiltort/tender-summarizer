from functools import lru_cache

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from src.apps.tender.services.pdf_parser import PDFParser
from src.apps.tender.services.llm_service import LLMService
from src.core.exceptions import PDFProcessingError, LLMServiceError
from src.apps.tender.schemas import TenderSummaryResponse, ErrorResponse

tender_router = APIRouter(prefix="/tender", tags=["tender summary"])


@lru_cache
def get_pdf_parser() -> PDFParser:
    return PDFParser()


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService()


@tender_router.post(
    "/summarize",
    response_model=TenderSummaryResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def summarize_tender(
    file: UploadFile = File(...),
    pdf_parser: PDFParser = Depends(get_pdf_parser),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Загрузите PDF-файл с тендерной документацией и получите структурированную выжимку.
    """
    try:
        raw_text = await pdf_parser.extract_text(file)

        result = await llm_service.summarize_tender(raw_text)

        return result

    except PDFProcessingError as e:
        raise HTTPException(status_code=400, detail={"error": str(e)})
    except LLMServiceError as e:
        raise HTTPException(status_code=503, detail={"error": str(e)})
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": f"Внутренняя ошибка сервера: {str(e)}"}
        )
