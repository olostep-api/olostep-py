from __future__ import annotations

import json
from typing import Any
from pydantic import ValidationError

from ..api_endpoints import EndpointContract
from ..errors import (
    OlostepAPIError,
    OlostepAuthenticationError,
    OlostepConnectionError,
    OlostepLikelyInvalidRequestError,
    OlostepRateLimitError,
)
from .transport import Transport


class EndpointCaller:
    def __init__(self, transport: Transport, base_url: str, api_key: str) -> None:
        self._t = transport
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    def _split_params(self, contract: EndpointContract, args: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        path = {k: args[k] for k in contract.path_parameters if k in args}
        query = {k: args[k] for k in contract.query_parameters if k in args}
        return path, query

    def _handle_errors(self, status: int, headers: dict[str, str], body: str, url: str, method: str) -> None:
        if status == 402:
            raise OlostepAuthenticationError(status_code=status, api_key=self._api_key)
        if status == 429:
            raise OlostepRateLimitError(status_code=status, message="Rate limit exceeded")
        if status >= 500:
            raise OlostepConnectionError(f"Server error: {status}")
        if status >= 400:
            error_type = headers.get("x-amzn-ErrorType")
            if (
                status == 403
                and error_type == "IncompleteSignatureException"
                and "Invalid key=value pair" in body
            ):
                raise OlostepLikelyInvalidRequestError(
                    status_code=status,
                    message="Request malformed - likely incorrect URL format or parameters",
                    response_data={"body": body, "headers": headers},
                    request_url=url,
                    request_method=method,
                )
            raise OlostepAPIError(status_code=status, message=f"{body}", response_data={"body": body, "headers": headers})

    async def invoke(
        self,
        contract: EndpointContract,
        *,
        args: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None
    ) -> Any:
        """
        Execute endpoint and return the parsed Pydantic response model instance.
        """
        args = args or {}
        path, query = self._split_params(contract, args)
        url = contract.build_url(self._base_url, **path)

        if contract.request_model is not None:
            try:
                _ = contract.request_model(**(body or args))
            except ValidationError:
                raise

        payload = None
        if contract.method != "GET" and contract.request_model is not None:
            try:
                req = contract.request_model(**(body or args))
                payload = req.model_dump(exclude_none=True)
            except ValidationError:
                raise

        status, headers, text = await self._t.request(
            contract.method, url, json=payload, params=query, headers=None
        )

        if status >= 400:
            self._handle_errors(status, headers, text, url, contract.method)

        data = json.loads(text or "{}")
        try:
            return contract.response_model(**data) if contract.response_model else data
        except ValidationError:
            raise