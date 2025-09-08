from __future__ import annotations

import aiohttp
import re
import time
from typing import Any, Protocol, Iterable, Callable

from pydantic import BaseModel

from ..config import USER_AGENT
from ..api_endpoints import CONTRACTS, EndpointContract


class Transport(Protocol):
    async def request(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], str]:
        ...


class AiohttpTransport:
    def __init__(self, api_key: str) -> None:
        # connector = aiohttp.TCPConnector(resolver=aiohttp.resolver.ThreadedResolver())
        self._session = aiohttp.ClientSession(
            # connector=connector,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
            }
        )

    async def close(self) -> None:
        await self._session.close()

    async def request(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], str]:
        hdrs = headers or {}
        async with self._session.request(method, url, json=json, params=params, headers=hdrs) as r:
            text = await r.text()
            return r.status, dict(r.headers), text


class FakeTransport:
    def __init__(
        self,
        responses: dict[tuple[str, str], dict[str, Any]] | None = None,
        *,
        fail: dict[tuple[str, str], dict[str, Any]] | None = None,
    ) -> None:
        self._responses = responses or {}
        self._fail = fail or {}

    async def request(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], str]:
        import json as _json
        from urllib.parse import urlsplit

        split = urlsplit(url)
        path = split.path
        key = (method.upper(), path)

        if key in self._fail:
            cfg = self._fail[key]
            if "exception" in cfg:
                exc = cfg["exception"]
                if exc == "connection":
                    raise ConnectionError("Simulated connection error")
                if exc == "timeout":
                    raise TimeoutError("Simulated timeout")
                if exc == "session":
                    raise RuntimeError("Simulated session error")
            status = int(cfg.get("status", 500))
            body = cfg.get("body", {})
            return status, {}, _json.dumps(body) if isinstance(body, dict) else str(body)

        if key in self._responses:
            return 200, {}, _json.dumps(self._responses[key])

        if path.endswith("/scrapes") and method.upper() == "POST":
            body = {
                "id": "scrape_fake_1",
                "object": "scrape",
                "created": 1,
                "retrieve_id": "ret_1",
                "url_to_scrape": (json or {}).get("url_to_scrape", ""),
                "result": {"html_content": "<html></html>", "size_exceeded": False},
            }
            return 200, {}, _json.dumps(body)
        if "/scrapes/" in path and method.upper() == "GET":
            sid = path.rsplit("/", 1)[-1]
            body = {
                "id": sid,
                "object": "scrape",
                "created": 1,
                "retrieve_id": "ret_1",
                "url_to_scrape": "https://example.com",
                "result": {"html_content": "<html></html>", "size_exceeded": False},
            }
            return 200, {}, _json.dumps(body)
        if path.endswith("/batches") and method.upper() == "POST":
            body = {
                "id": "batch_fake_1",
                "object": "batch",
                "status": "in_progress",
                "created": 1,
                "total_urls": len((json or {}).get("items", [])),
                "completed_urls": 0,
                "parser": {"id": (json or {}).get("parser", {}).get("id", "default")},
                "country": (json or {}).get("country", "US"),
            }
            return 200, {}, _json.dumps(body)
        if "/batches/" in path and method.upper() == "GET":
            parts = path.strip("/").split("/")
            if parts[-1] != "items":
                body = {
                    "id": parts[-1],
                    "batch_id": parts[-1],
                    "object": "batch",
                    "status": "in_progress",
                    "created": 1,
                    "total_urls": 2,
                    "completed_urls": 1,
                    "number_retried": 0,
                    "parser": "default",
                    "start_date": "2024-01-01T00:00:00Z",
                }
            else:
                body = {
                    "batch_id": parts[-2],
                    "object": "batch",
                    "status": "in_progress",
                    "items": [
                        {"custom_id": "item1", "retrieve_id": "ret_1", "url": "https://a"},
                        {"custom_id": "item2", "retrieve_id": "ret_2", "url": "https://b"},
                    ],
                    "items_count": 2,
                    "cursor": 1,
                }
            return 200, {}, _json.dumps(body)
        if path.endswith("/crawls") and method.upper() == "POST":
            body = {
                "id": "crawl_fake_1",
                "object": "crawl",
                "status": "in_progress",
                "created": 1,
                "start_date": "2024-01-01T00:00:00Z",
                "start_url": (json or {}).get("start_url", ""),
                "max_pages": (json or {}).get("max_pages", 10),
                "max_depth": (json or {}).get("max_depth"),
                "exclude_urls": (json or {}).get("exclude_urls"),
                "include_urls": (json or {}).get("include_urls", ["/**"]),
                "include_external": (json or {}).get("include_external", False),
                "search_query": (json or {}).get("search_query"),
                "top_n": (json or {}).get("top_n"),
                "current_depth": 0,
                "pages_count": 0,
                "webhook_url": (json or {}).get("webhook_url"),
            }
            return 200, {}, _json.dumps(body)
        if path.endswith("/pages") and "/crawls/" in path and method.upper() == "GET":
            cid = path.split("/")[-3] if path.endswith("/pages") else path.split("/")[-2]
            body = {
                "crawl_id": cid,
                "object": "crawl",
                "status": "in_progress",
                "search_query": (params or {}).get("search_query"),
                "pages_count": 2,
                "pages": [
                    {"id": "p1", "retrieve_id": "ret_1", "url": "https://p1", "is_external": False},
                    {"id": "p2", "retrieve_id": "ret_2", "url": "https://p2", "is_external": True},
                ],
                "metadata": {"external_urls": ["https://p2"], "failed_urls": []},
                "cursor": 1,
            }
            return 200, {}, _json.dumps(body)
        if "/crawls/" in path and method.upper() == "GET":
            cid = path.strip("/").split("/")[-1]
            body = {
                "id": cid,
                "object": "crawl",
                "status": "in_progress",
                "created": 1,
                "start_date": "2024-01-01T00:00:00Z",
                "start_url": "https://example.com",
                "max_pages": 10,
                "max_depth": None,
                "exclude_urls": None,
                "include_urls": ["/**"],
                "include_external": False,
                "search_query": None,
                "top_n": None,
                "current_depth": 1,
                "pages_count": 1,
                "webhook_url": None,
            }
            return 200, {}, _json.dumps(body)
        if path.endswith("/maps") and method.upper() == "POST":
            body = {
                "urls_count": 3,
                "urls": ["https://a", "https://b", "https://c"],
                "id": "map_1",
                "cursor": "next_1",
            }
            return 200, {}, _json.dumps(body)
        if path.endswith("/retrieve") and method.upper() == "GET":
            body = {
                "html_content": None,
                "markdown_content": None,
                "json_content": {},
                "html_hosted_url": None,
                "markdown_hosted_url": None,
                "json_hosted_url": None,
                "size_exceeded": False,
            }
            return 200, {}, _json.dumps(body)

        return 200, {}, "{}"


# ============ Schema-driven smart fake ============

class FakeTransportSmart(Transport):
    def __init__(
        self,
        contracts: Iterable[EndpointContract] | None = None,
        *,
        overrides: dict[tuple[str, str], dict[str, Any]] | None = None,
        fail: dict[tuple[str, str], dict[str, Any]] | None = None,
        seed: int | None = None,
    ) -> None:
        self._contracts = list(contracts) if contracts is not None else list(CONTRACTS.values())
        self._overrides = overrides or {}
        self._fail = fail or {}
        self._seed = seed or 0
        self._compiled = [self._compile_pattern(c) for c in self._contracts]

    def _compile_pattern(self, c: EndpointContract) -> tuple[EndpointContract, re.Pattern[str]]:
        # Build a regex that matches any prefix before the path and captures path params
        # Example: /batches/{batch_id}/items -> ^.*/batches/(?P<batch_id>[^/]+)/items$
        pattern = re.sub(r"{([^}]+)}", lambda m: f"(?P<{m.group(1)}>[^/]+)", c.path)
        regex = re.compile(rf"^.*/?{pattern.lstrip('/')}$")
        return c, regex

    def _auto_value(self, annotation: Any, name: str) -> Any:
        try:
            from enum import Enum
            from typing import get_origin, get_args
        except Exception:
            return None
        origin = get_origin(annotation)
        args = get_args(annotation)
        if origin is None:
            if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                return self._auto_model(annotation)
            if isinstance(annotation, type) and issubclass(annotation, Enum):
                return list(annotation)[0]
            if annotation in (str,):
                return f"fake_{name}"
            if annotation in (int,):
                return 1
            if annotation in (float,):
                return 1.0
            if annotation in (bool,):
                return False
            if annotation in (dict,):
                return {}
            if annotation in (list,):
                return []
            return None
        if origin in (list, list[Any]):
            return []
        if origin in (dict, dict[str, Any]):
            return {}
        # Optional/Union -> pick first non-None
        if origin is None and annotation is None:
            return None
        if origin is not None and args:
            non_none = [a for a in args if a is not type(None)]  # noqa: E721
            if non_none:
                return self._auto_value(non_none[0], name)
        return None

    def _auto_model(self, model_type: type[BaseModel]) -> BaseModel:
        kwargs: dict[str, Any] = {}
        for fname, field in model_type.model_fields.items():
            if field.default is not None:
                kwargs[fname] = field.default
                continue
            val = self._auto_value(field.annotation, fname)
            if val is None and field.is_required():
                # basic defaults for common primitives
                if field.annotation in (str,):
                    val = f"fake_{fname}"
                elif field.annotation in (int,):
                    val = 1
                elif field.annotation in (bool,):
                    val = False
                else:
                    val = None
            kwargs[fname] = val
        return model_type(**kwargs)  # type: ignore[call-arg]

    def _enrich(self, c: EndpointContract, *, path_params: dict[str, str], query: dict[str, Any], body: dict[str, Any], model: BaseModel) -> BaseModel:
        key = c.key
        update: dict[str, Any] = {}
        if key == ("scrape", "url"):
            update = {
                "id": model.__dict__.get("id") or "scrape_fake_1",
                "created": int(time.time()),
                "retrieve_id": model.__dict__.get("retrieve_id") or "ret_1",
                "url_to_scrape": body.get("url_to_scrape", ""),
                "result": {"html_content": "<html></html>", "size_exceeded": False},
            }
        elif key == ("scrape", "get"):
            update = {
                "id": path_params.get("scrape_id", "scrape_fake_1"),
                "created": int(time.time()),
                "retrieve_id": "ret_1",
                "url_to_scrape": "https://example.com",
                "result": {"html_content": "<html></html>", "size_exceeded": False},
            }
        elif key == ("batch", "start"):
            update = {
                "id": "batch_fake_1",
                "status": model.__dict__.get("status") or "in_progress",
                "created": int(time.time()),
                "total_urls": len(body.get("items", [])),
                "completed_urls": 0,
            }
        elif key == ("batch", "items"):
            bid = path_params.get("batch_id") or query.get("batch_id", "batch_fake_1")
            items = [
                {"custom_id": "item1", "retrieve_id": "ret_1", "url": "https://a"},
                {"custom_id": "item2", "retrieve_id": "ret_2", "url": "https://b"},
            ]
            update = {
                "batch_id": bid,
                "status": "in_progress",
                "items": items,
                "items_count": len(items),
                "cursor": 1,
            }
        elif key == ("crawl", "start"):
            update = {
                "id": "crawl_fake_1",
                "status": "in_progress",
                "created": int(time.time()),
                "start_date": "2024-01-01T00:00:00Z",
                "start_url": body.get("start_url", ""),
                "max_pages": body.get("max_pages", 10),
                "include_urls": body.get("include_urls", ["/**"]),
                "include_external": bool(body.get("include_external", False)),
                "pages_count": 0,
            }
        elif key == ("crawl", "pages"):
            cid = path_params.get("crawl_id", "crawl_fake_1")
            pages = [
                {"id": "p1", "retrieve_id": "ret_1", "url": "https://p1", "is_external": False},
                {"id": "p2", "retrieve_id": "ret_2", "url": "https://p2", "is_external": True},
            ]
            update = {
                "crawl_id": cid,
                "status": "in_progress",
                "search_query": query.get("search_query"),
                "pages": pages,
                "pages_count": len(pages),
                "cursor": 1,
                "metadata": {"external_urls": ["https://p2"], "failed_urls": []},
            }
        elif key == ("map", "create"):
            urls = ["https://a", "https://b", "https://c"]
            update = {"urls": urls, "urls_count": len(urls), "id": "map_1", "cursor": "next_1"}
        elif key == ("retrieve", "get"):
            fmts = query.get("formats") or []
            payload: dict[str, Any] = {"size_exceeded": False}
            if "html" in fmts:
                payload["html_content"] = "<html></html>"
            if "markdown" in fmts:
                payload["markdown_content"] = "# md"
            if "json" in fmts:
                payload["json_content"] = {}
            update = payload
        if update:
            try:
                return model.model_copy(update=update)
            except Exception:
                # fallback: reconstruct
                data = model.model_dump(mode="python")
                data.update(update)
                return model.__class__(**data)
        return model

    async def request(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], str]:
        import json as _json
        from urllib.parse import urlsplit

        split = urlsplit(url)
        path = split.path

        # overrides / failures by exact (method, path)
        if (method.upper(), path) in self._fail:
            cfg = self._fail[(method.upper(), path)]
            if "exception" in cfg:
                exc = cfg["exception"]
                if exc == "connection":
                    raise ConnectionError("Simulated connection error")
                if exc == "timeout":
                    raise TimeoutError("Simulated timeout")
                if exc == "session":
                    raise RuntimeError("Simulated session error")
            status = int(cfg.get("status", 500))
            body = cfg.get("body", {})
            return status, {}, _json.dumps(body) if isinstance(body, dict) else str(body)
        if (method.upper(), path) in self._overrides:
            return 200, {}, _json.dumps(self._overrides[(method.upper(), path)])

        # match contract
        matched: EndpointContract | None = None
        path_params: dict[str, str] = {}
        for c, rx in self._compiled:
            if c.method.upper() != method.upper():
                continue
            m = rx.match(path)
            if m:
                matched = c
                path_params = m.groupdict()
                break
        if not matched or not matched.response_model:
            return 200, {}, "{}"

        # build model
        model = self._auto_model(matched.response_model)  # type: ignore[arg-type]
        model = self._enrich(matched, path_params=path_params, query=(params or {}), body=(json or {}), model=model)
        return 200, {}, model.model_dump_json()  # type: ignore[call-arg] 