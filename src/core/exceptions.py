class AppException(Exception):
    pass


class PDFProcessingError(AppException):
    pass


class LLMServiceError(AppException):
    pass
