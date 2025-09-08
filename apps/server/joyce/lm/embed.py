from __future__ import annotations

from openai import AsyncOpenAI

client = AsyncOpenAI()


async def embed_text(text: str) -> list[float]:
    response = await client.embeddings.create(
        input=text, model="text-embedding-3-small"
    )

    return response.data[0].embedding


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    response = await client.embeddings.create(
        input=texts, model="text-embedding-3-small"
    )

    return [data.embedding for data in response.data]
