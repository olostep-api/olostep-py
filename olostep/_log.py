"""
Modern logging configuration for Olostep SDK.

Provides library-safe logging with secret redaction and structured IO logging.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .config import IO_LOG_PATH

# Top-level package logger
logger = logging.getLogger("olostep")
logger.addHandler(logging.NullHandler())   # library-safe default
logger.propagate = True                    # let app handlers catch logs

# Sub-loggers (optional convenience)
io_logger = logging.getLogger("olostep.backend.io")
io_logger.propagate = True # it's the default, just to be explicit


class RedactSecretsFilter(logging.Filter):
    """
    Redacts common secrets in log records. Users may attach this to their handlers.
    """
    SECRET_PATTERNS: Iterable[re.Pattern[str]] = (
        re.compile(r"(Authorization:\s*Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*", re.I),
        re.compile(r"(api[_-]?key=)[A-Za-z0-9]{10,}", re.I),
        re.compile(r"(token=)[A-Za-z0-9\-_\.]{10,}", re.I),
        re.compile(r"(\"authorization\":\s*\"Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*", re.I),
        re.compile(r"(\"Authorization\":\s*\"Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*", re.I),
        re.compile(r"(\"x-api-key\":\s*\")[A-Za-z0-9]{10,}", re.I),
        re.compile(r"(\"x-auth-token\":\s*\")[A-Za-z0-9\-_\.]{10,}", re.I),
    )
    REPLACEMENT = r"\1[REDACTED]"

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for pat in self.SECRET_PATTERNS:
            msg = pat.sub(self.REPLACEMENT, msg)
        # stash sanitized message without mutating args (safe for %-formatting)
        record.msg = msg
        record.args = ()
        return True


class PerMessageIOFilter(logging.Filter):
    """
    Filter that allows per-message control of IO logging.
    Use the 'log_to_file' extra parameter to control whether a message gets logged to file.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        skip_file_logging = getattr(record, 'skip_file_logging', False)
        return not skip_file_logging

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# functions to toggle logging behavior
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def _enable_stderr_debug(level: int = logging.DEBUG) -> None:
    """
    Opt-in helper: attach a simple stderr handler to the package logger.
    Safe for quickstarts; in real apps users should configure logging themselves.
    """
    h = logging.StreamHandler()
    fmt = "[%(levelname)s] %(name)s: %(message)s"
    h.setFormatter(logging.Formatter(fmt))
    h.addFilter(RedactSecretsFilter())
    root = logging.getLogger("olostep")
    root.setLevel(level)
    root.addHandler(h)

# Setup IO logger with file handler if logging is enabled
def _setup_io_file_handler() -> None:
    logger.warning("Setting up IO file logging. This is a lot of data.")
    """Setup file handler for IO logger if logging is enabled."""
    # try:
    #     from .config import IO_LOG_PATH
    # except ImportError:
    #     # Fallback when not imported as part of package
    #     IO_LOG_PATH = os.getenv("OLOSTEP_IO_LOG_PATH", "tests/runtime")

    if not IO_LOG_PATH:
        return
    
    # Check if file handler already exists
    if any(isinstance(h, logging.FileHandler) for h in io_logger.handlers):
        return
    
    # Create log directory
    log_dir = Path(IO_LOG_PATH)
    logger.info(f"Logging IO to: {log_dir.resolve()}")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create file handler with JSON formatter
    file_handler = logging.FileHandler(log_dir / "io_logs.json", mode='a')
    file_handler.setLevel(logging.DEBUG)
    
    # Custom formatter for structured JSON logging
    class IOJSONFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            
            # Add i and o data if present, with redaction (handle both cases)

            if hasattr(record, 'request_id'):
                log_entry["request_id"] = record.request_id

            if hasattr(record, 'response_time_ms'):
                log_entry["response_time_ms"] = record.response_time_ms

            if hasattr(record, 'i'):
                log_entry["I"] = self._redact_data(record.i)
            elif hasattr(record, 'I'):
                log_entry["I"] = self._redact_data(record.I)

            if hasattr(record, 'o'):
                log_entry["O"] = self._redact_data(record.o)
            elif hasattr(record, 'O'):
                log_entry["O"] = self._redact_data(record.O)
            

            return json.dumps(log_entry, indent=2) + ","
        
        def _redact_data(self, data: Any) -> Any:
            """Recursively redact sensitive data from dictionaries."""
            if isinstance(data, dict):
                redacted = {}
                for key, value in data.items():
                    if key == "body" and isinstance(value, str):
                        # Always try to parse body as JSON first, then handle as text
                        try:
                            parsed_body = json.loads(value)
                            redacted[key] = self._redact_data(parsed_body)
                        except (json.JSONDecodeError, TypeError):
                            # If not valid JSON, keep as string but redact secrets
                            if self._contains_secret(value):
                                redacted[key] = self._redact_string(value)
                            else:
                                redacted[key] = value
                    elif isinstance(value, str) and self._contains_secret(value):
                        redacted[key] = self._redact_string(value)
                    elif isinstance(value, dict):
                        redacted[key] = self._redact_data(value)
                    else:
                        redacted[key] = value
                return redacted
            elif isinstance(data, str) and self._contains_secret(data):
                return self._redact_string(data)
            else:
                return data
        
        def _contains_secret(self, text: str) -> bool:
            """Check if text contains secrets."""
            # Check for Bearer tokens in any case
            if re.search(r'bearer\s+[a-za-z0-9\-\._~\+\/]+=*', text, re.I):
                return True
            # Check for API keys
            if re.search(r'api[_-]?key[=:]\s*[a-za-z0-9]{10,}', text, re.I):
                return True
            # Check for tokens
            if re.search(r'token[=:]\s*[a-za-z0-9\-_\.]{10,}', text, re.I):
                return True
            return False
        
        def _redact_string(self, text: str) -> str:
            """Redact secrets in a string."""
            # Redact Bearer tokens
            text = re.sub(r'(bearer\s+)[a-za-z0-9\-\._~\+\/]+=*', r'\1[REDACTED]', text, flags=re.I)
            # Redact API keys
            text = re.sub(r'(api[_-]?key[=:]\s*)[a-za-z0-9]{10,}', r'\1[REDACTED]', text, flags=re.I)
            # Redact tokens
            text = re.sub(r'(token[=:]\s*)[a-za-z0-9\-_\.]{10,}', r'\1[REDACTED]', text, flags=re.I)
            return text
    
    file_handler.setFormatter(IOJSONFormatter())
    file_handler.addFilter(RedactSecretsFilter())
    file_handler.addFilter(PerMessageIOFilter())
    io_logger.addHandler(file_handler)
    
    io_logger.setLevel(logging.DEBUG)




def get_logger(name: str | None = None) -> logging.Logger:
    """Library API for internal modules."""
    return logging.getLogger("olostep" + ("" if not name else f".{name}"))


def load_io_logs(log_file_path: str | Path) -> list[dict[str, Any]]:
    """
    Load IO logs from a file as a list of dictionaries.
    
    The log file contains JSON objects separated by commas.
    This function wraps the content in square brackets to create a valid JSON array.
    
    Args:
        log_file_path: Path to the IO logs JSON file
        
    Returns:
        List of log entries as dictionaries
        
    Raises:
        FileNotFoundError: If the log file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    log_path = Path(log_file_path)
    
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")
    
    with open(log_path, 'r') as f:
        content = f.read().strip()
    
    if not content:
        return []
    
    # Remove trailing comma if present
    if content.endswith(','):
        content = content[:-1]
    
    # Wrap in square brackets to create a valid JSON array
    json_array_content = f"[{content}]"
    
    return json.loads(json_array_content)


