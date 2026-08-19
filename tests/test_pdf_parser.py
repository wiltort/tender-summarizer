from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile

from src.apps.tender.services.pdf_parser import PDFParser
from src.core.config import settings
from src.core.exceptions import PDFProcessingError

VALID_PDF_HEADER = b"%PDF-1.7\n..."


def _make_upload(content: bytes, filename: str = "tender.pdf") -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content))


@pytest.mark.asyncio
async def test_extract_text_rejects_oversized_file():
    parser = PDFParser()
    content = b"%PDF" + b"x" * (settings.pdf_max_size + 1)

    with pytest.raises(PDFProcessingError, match="Размер файла превышает"):
        await parser.extract_text(_make_upload(content))


@pytest.mark.asyncio
async def test_extract_text_rejects_non_pdf():
    parser = PDFParser()

    with pytest.raises(PDFProcessingError, match="не является PDF"):
        await parser.extract_text(_make_upload(b"PK\x03\x04 not a pdf"))


@pytest.mark.asyncio
async def test_extract_text_returns_joined_pages():
    parser = PDFParser()

    page_a = MagicMock()
    page_a.extract_text.return_value = "Страница 1"
    page_b = MagicMock()
    page_b.extract_text.return_value = "Страница 2"
    empty_page = MagicMock()
    empty_page.extract_text.return_value = None

    pdf_mock = MagicMock()
    pdf_mock.__enter__.return_value.pages = [page_a, page_b, empty_page]

    with patch(
        "src.apps.tender.services.pdf_parser.pdfplumber.open",
        return_value=pdf_mock,
    ):
        result = await parser.extract_text(_make_upload(VALID_PDF_HEADER))

    assert result == "Страница 1\nСтраница 2"


@pytest.mark.asyncio
async def test_extract_text_rejects_scanned_pdf():
    parser = PDFParser()

    blank_page = MagicMock()
    blank_page.extract_text.return_value = None

    pdf_mock = MagicMock()
    pdf_mock.__enter__.return_value.pages = [blank_page]

    with patch(
        "src.apps.tender.services.pdf_parser.pdfplumber.open",
        return_value=pdf_mock,
    ):
        with pytest.raises(PDFProcessingError, match="отсканированным изображением"):
            await parser.extract_text(_make_upload(VALID_PDF_HEADER))


@pytest.mark.asyncio
async def test_extract_text_wraps_parsing_errors():
    parser = PDFParser()

    pdf_mock = MagicMock()
    pdf_mock.__enter__.side_effect = RuntimeError("corrupted")

    with patch(
        "src.apps.tender.services.pdf_parser.pdfplumber.open",
        return_value=pdf_mock,
    ):
        with pytest.raises(PDFProcessingError, match="Ошибка при чтении PDF"):
            await parser.extract_text(_make_upload(VALID_PDF_HEADER))
