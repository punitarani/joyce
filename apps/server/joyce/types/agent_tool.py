from __future__ import annotations

from typing import ClassVar, Dict

from pydantic import BaseModel


class AgentTool(BaseModel):
    """
    Lightweight base class for tool parameter models.

    - Subclass this for any function tool parameter model
    - Keep subclasses minimal: only field names and types
    - Use `.raw_schema` to export an OpenAI/JSONSchema-compatible schema

    This is designed to work with LiveKit's `@function_tool(raw_schema=...)`.
    """

    # Allow subclasses to opt out of additional properties if needed
    allow_additional_properties: ClassVar[bool] = False
    # Concrete subclasses will get this populated automatically
    raw_schema: ClassVar[Dict]

    @classmethod
    def _build_raw_schema(cls) -> Dict:
        """Return a JSON Schema dict suitable for OpenAI/LiveKit raw_schema.

        - type: object
        - properties: Pydantic-generated properties
        - required: fields without defaults
        - additionalProperties: False by default for stricter validation
        """
        schema = cls.model_json_schema()

        properties = schema.get("properties", {})

        # Compute required: fields without defaults/default_factory
        required_fields: list[str] = []
        for field_name, field_info in cls.model_fields.items():
            # Pydantic v2 FieldInfo exposes `is_required()`
            is_required = False
            try:
                is_required = bool(field_info.is_required())  # type: ignore[attr-defined]
            except Exception:
                # Fallback: treat as required if neither default nor factory present
                is_required = (
                    field_info.default is ... and field_info.default_factory is None
                )

            if is_required:
                required_fields.append(field_name)

        result: Dict = {
            "type": "object",
            "properties": properties,
        }
        if required_fields:
            result["required"] = required_fields

        if not cls.allow_additional_properties:
            result["additionalProperties"] = False

        return result

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Skip base class itself
        if cls is AgentTool:
            return
        # Build and attach class-level raw schema for decorator usage
        cls.raw_schema = cls._build_raw_schema()
