import copy


def json_merge_patch(target: dict, patch: dict) -> dict:
    """
    Apply a JSON Merge Patch (RFC 7396).
    - target: original JSON (dict, list, or primitive)
    - patch: patch JSON (dict, list, or primitive)

    Args:
        target: Original JSON (dict, list, or primitive)
        patch: Patch JSON (dict, list, or primitive)

    Returns:
        Merged dictionary

    Examples:
        target = {"a": "b", "c": {"d": "e", "f": "g"}}
        patch = {"a": "z", "c": {"f": null}}
        result = {"a": "z", "c": {"d": "e"}}
    """
    if not isinstance(patch, dict):
        return copy.deepcopy(patch)

    if not isinstance(target, dict):
        target = {}

    result = copy.deepcopy(target)

    for key, value in patch.items():
        if value is None:
            # Remove key if exists
            result.pop(key, None)
        else:
            result[key] = json_merge_patch(result.get(key), value)

    return result
