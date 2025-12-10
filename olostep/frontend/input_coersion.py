""" This file contains helper functions that enable the frontend layer to 
offer nice input coercion to the user.
Input validation is a non-goal! Coersion happens before validation.
"""

from typing import Any
import json
from pydantic import BaseModel

def coerce_to_list(value: Any) -> list[Any]:
    if value is None:
        return value
    if not isinstance(value, list):
        return [value]
    return value

def coerce_to_key_in_dict(value: Any, key: str) -> dict[str, Any]:
    if value is None:
        return value
    if isinstance(value, BaseModel):
        return value
    if not isinstance(value, dict):
        return {key: value}
    return value

def coerce_to_string(value: Any) -> str:
    if value is None:
        return value
    if isinstance(value, list):
        return json.dumps(value)
        # catch at end
    if isinstance(value, dict):
        return json.dumps(value)
    if isinstance(value, str):
        return value
    raise ValueError(f"Cannot coerce {value} to string")