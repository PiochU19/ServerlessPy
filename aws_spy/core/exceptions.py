import typing_extensions as te


class BaseSpyAppError(Exception):
    ...


class RouteDefinitionError(BaseSpyAppError):
    ...


class FunctionDefinitionError(BaseSpyAppError):
    ...


class BaseSpyError(Exception):
    def __init__(
        self: te.Self,
        error: str | list[str],
        *,
        status_code: int = 400,
        additional_headers: dict[str, str] | None = None,
    ) -> None:
        self.error = error
        # for ErrorResponse
        self.status_code = status_code
        self.additional_headers = additional_headers
