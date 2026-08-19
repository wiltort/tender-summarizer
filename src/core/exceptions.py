class AppException(Exception):
    pass


class PDFException(AppException):
    pass


class LLMServiceException(AppException):
    pass
