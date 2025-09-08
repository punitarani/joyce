from __future__ import annotations

import json

from joyce.db.schema import UserEntity
from joyce.utils.tabulate import db_entities_to_markdown


def format_user_entity(entity: UserEntity | None) -> str:
    if entity is None:
        return "No entity found"
    return json.dumps(entity.serialize())


def format_user_entities(entities: list[UserEntity]) -> str:
    return db_entities_to_markdown(entities)
