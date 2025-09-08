"""
Olostep API SDK Exceptions.

This module defines the exception hierarchy for the Olostep API SDK,
providing specific error types for different failure scenarios.
"""

from typing import Any


class OlostepBaseError(Exception):
    """Base exception for all Olostep API errors."""
    
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

class OlostepAsyncContextError(OlostepBaseError):
    """Raised when an async context is required but not provided."""
    
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

class OlostepBetaFeatureError(OlostepBaseError):
    """Raised when a beta feature is used and the client is not whitelisted."""
    
    def __init__(self, message: str) -> None:
        super().__init__(message)

class OlostepAPIError(OlostepBaseError):
    """Raised when the Olostep API returns an error response."""
    
    def __init__(
        self, 
        status_code: int, 
        message: str, 
        response_data: dict[str, Any] | None = None
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.response_data = response_data
        super().__init__(f"Olostep API error {status_code}: {message}")


class OlostepRateLimitError(OlostepAPIError):
    """Raised when rate limit is exceeded or payment is required."""
    
    def __init__(
        self, 
        status_code: int, 
        message: str, 
        response_data: dict[str, Any] | None = None
    ) -> None:
        super().__init__(status_code, message, response_data)


class OlostepAuthenticationError(OlostepAPIError):
    """Raised when API rejects the provided API key.
    The message reveals only half of the key (rounded down) and masks the rest.
    """
    msg_template = "The API rejected your API Key {masked} as invalid"
    
    def _mask_key_half(self, key: str) -> str:
        half = len(key) // 2
        if half <= 0:
            return "*****"
        return f"{key[:half]}*****"

    def __init__(
        self, 
        status_code: int, 
        api_key: str,
        response_data: dict[str, Any] | None = None
    ) -> None:

        masked = self._mask_key_half(api_key)
        message = self.msg_template.format(masked=masked)
        super().__init__(status_code, message, response_data)


class OlostepValidationError(OlostepBaseError):
    """Raised when request validation fails."""
    
    def __init__(self, message: str, field: str | None = None) -> None:
        self.field = field
        super().__init__(f"Validation error{f' in field {field}' if field else ''}: {message}")


class OlostepTimeoutError(OlostepBaseError):
    """Raised when a request times out."""
    
    def __init__(self, message: str, timeout_seconds: float | None = None) -> None:
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Timeout error{f' after {timeout_seconds}s' if timeout_seconds else ''}: {message}")


class OlostepConnectionError(OlostepBaseError):
    """Raised when connection to Olostep API fails."""
    
    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        self.original_error = original_error
        super().__init__(f"Connection error: {message}")


class OlostepLikelyInvalidRequestError(OlostepAPIError):
    """Raised when the API returns an IncompleteSignatureException.
    
    This error pattern indicates that the request was malformed in a way that
    prevented proper authentication signature generation. This is typically NOT
    an authentication issue, but rather indicates a problem with the request
    structure itself.
    
    Common causes:
    - Incorrect URL format (e.g., using path parameters instead of query parameters)
    - Malformed query parameters
    - Invalid request headers
    - Incorrect request body format
    
    When this error occurs, check:
    1. URL format and structure
    2. Query parameter formatting
    3. Request headers
    4. Request body (if applicable)
    
    Example:
        This error commonly occurs when using path parameters for endpoints
        that expect query parameters, such as:
        - Wrong: /retrieve/{retrieve_id}
        - Correct: /retrieve?retrieve_id=...&formats=...
    """
    
    def __init__(
        self, 
        status_code: int, 
        message: str, 
        response_data: dict[str, Any] | None = None,
        request_url: str | None = None,
        request_method: str | None = None
    ) -> None:
        self.request_url = request_url
        self.request_method = request_method
        
        # Add helpful debugging information to the message
        debug_info = []
        if request_url:
            debug_info.append(f"URL: {request_url}")
        if request_method:
            debug_info.append(f"Method: {request_method}")
        
        if debug_info:
            message = f"{message} | Request details: {' | '.join(debug_info)}"
        
        super().__init__(status_code, message, response_data)


class OlostepNoAPIKey(OlostepBaseError):
    """Raised when no API key is provided in init nor found in environment."""
    def __init__(self) -> None:
        super().__init__("Olostep API key is required and was neither provided nor found in the environment.") 