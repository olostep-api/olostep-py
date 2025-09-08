from . import api_endpoints  # EndpointContract definitions
from . import errors                # SDK error types
from . import config                # SDK config

# Backend (transport/validation)
from . import backend
from .backend import validation

# Clients
from . import clients
from .clients import async_client
from .clients import sync_client

# Frontend (stateful client responses + typed-dict UI)
from . import frontend
from .frontend import client_state
from .frontend.typed_dict import sdk
from .frontend.typed_dict import types

# Main exports for easy importing
from .clients.async_client import AsyncOlostepClient
from .clients.sync_client import OlostepClient
from .backend.validation import Format, Country, RetrieveFormat, Status
from .backend.transport import FakeTransport, AiohttpTransport
from .backend.caller import EndpointCaller
from .frontend.typed_dict.sdk import TypedDictFrontend

__version__ = "0.1.0"
__all__ = [
    "AsyncOlostepClient",
    "OlostepClient", 
    "Format",
    "Country",
    "RetrieveFormat",
    "Status",
    "FakeTransport",
    "AiohttpTransport",
    "EndpointCaller",
    "TypedDictFrontend",
    "api_endpoints",
    "errors",
    "config",
    "backend",
    "validation",
    "clients",
    "frontend",
    "client_state",
    "sdk",
    "types",
]