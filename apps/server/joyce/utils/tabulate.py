from __future__ import annotations

from sqlalchemy.inspection import inspect
from tabulate import tabulate

from joyce.db.schema.base import Base

from .string import serialize_value


def db_model_to_dict(obj: Base) -> dict[str, str]:
    """Turn a SQLAlchemy model into a dict of column -> serialized value."""
    return {
        c.key: serialize_value(getattr(obj, c.key))
        for c in inspect(obj).mapper.column_attrs
    }


def db_entities_to_markdown(entities: list[Base]) -> str:
    """Render a list of SQLAlchemy entities as a Markdown table."""
    if not entities:
        return ""

    dicts = [db_model_to_dict(e) for e in entities]
    headers = dicts[0].keys()
    rows = [d.values() for d in dicts]

    return tabulate(rows, headers=headers, tablefmt="github")
