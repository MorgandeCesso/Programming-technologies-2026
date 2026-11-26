class AppError(Exception):
    status = 500
    code = "internal_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class IndexEmpty(AppError):
    status = 409
    code = "index_empty"


class SqlError(AppError):
    status = 502
    code = "invalid_sql"


class LLMError(AppError):
    status = 502
    code = "llm_error"


class LLMInvalidResponse(LLMError):
    code = "llm_invalid_response"


class LLMUnavailable(LLMError):
    status = 503
    code = "llm_unavailable"


class LLMTimeout(LLMError):
    status = 504
    code = "llm_timeout"
