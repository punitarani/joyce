from __future__ import annotations

import math
from datetime import datetime, timezone


def calculate_hybrid_score(
    distance: float,
    created_at: str,
    recency_weight: float = 0.15,
    recency_decay_days: float = 90.0,
) -> float:
    """
    Calculate hybrid score combining similarity and recency.

    Based on research-backed approach:
    - Converts distance to similarity (normalized 0-1)
    - Applies gentle recency boost only when items are close in similarity
    - Uses exponential decay with configurable half-life

    Args:
        distance: ChromaDB L2 distance (lower = more similar)
        created_at: ISO timestamp when memory was created
        recency_weight: Weight for recency component (0.1-0.2 recommended)
        recency_decay_days: Days for recency to decay to ~37% (1/e)

    Returns:
        Combined score where higher = better
    """
    # Convert distance to normalized similarity (0-1, higher = more similar)
    similarity = 1.0 / (1.0 + distance)

    # Calculate age in days
    try:
        timestamp = created_at.replace("Z", "+00:00")
        dt = datetime.fromisoformat(timestamp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0
        age_days = max(0.0, age_days)
    except (ValueError, AttributeError):
        age_days = recency_decay_days * 2  # Treat invalid timestamps as old

    # Exponential decay recency factor (0-1, higher = more recent)
    recency = math.exp(-age_days / recency_decay_days)

    # Hybrid score: primarily similarity with gentle recency boost
    # This ensures recency only matters when similarities are close
    return similarity * (1.0 + recency_weight * recency)
