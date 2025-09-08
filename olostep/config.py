from __future__ import annotations

import os
from typing import Final

# SDK version
VERSION: Final[str] = "0.1.0"

# Base API URL (can be overridden via env)
BASE_API_URL: Final[str] = os.getenv("OLOSTEP_BASE_API_URL", "https://api.olostep.com/v1")

# User-Agent header built from version
USER_AGENT: Final[str] = f"olostep-python-sdk/{VERSION}"

# Environment variable names to try for API key (first hit wins)
API_KEY_ENV: Final[str] | None = os.getenv("OLOSTEP_API_KEY")
