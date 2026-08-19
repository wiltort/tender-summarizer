import io
import pdfplumber
from fastapi import UploadFile
from src.core.exceptions import PDFProcessingError
from src.core.config import settings


class PDFParser:
    """Класс для извлечения текста из PDF файлов."""

    async def extract_text(self, file: UploadFile) -> str:
        """
        Асинхронно извлекает текст из загруженного PDF.

        Args:
            file: Загруженный PDF-файл (FastAPI UploadFile).

        Returns:
            Извлечённый текст.

        Raises:
            PDFProcessingError: Если файл не PDF или не удалось извлечь текст.
        """

        content = await file.read()
        if len(content) > settings.pdf_max_size:
            raise PDFProcessingError(
                f"Размер файла превышает {settings.pdf_max_size // (1024 * 1024)} MB."
            )

        if not content.startswith(b"%PDF"):
            raise PDFProcessingError("Загруженный файл не является PDF.")

        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                extracted_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"

                if not extracted_text.strip():
                    raise PDFProcessingError(
                        "Не удалось извлечь текст из PDF. Файл может быть отсканированным изображением."
                    )

                return extracted_text.strip()

        except Exception as e:
            raise PDFProcessingError(f"Ошибка при чтении PDF: {str(e)}")
