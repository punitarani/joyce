import datetime
import json
import re
from typing import Any


def safify(string: str) -> str:
    """
    Make a string safe for use in a URL.
    Removes special characters and spaces, and converts to lowercase with spaces replaced by hyphens.
    """
    pattern = re.compile(r"[^a-z0-9\-_./]+")
    return pattern.sub("", string.strip().lower().replace(" ", "-"))


def serialize_value(value: Any) -> str:
    """Convert SQLAlchemy column values to str safely."""
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value) if value is not None else ""
