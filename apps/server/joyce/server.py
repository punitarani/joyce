from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from pydantic import BaseModel

from .env import env


class TokenRequest(BaseModel):
    room_name: str
    participant_name: str


class TokenResponse(BaseModel):
    token: str
    room_name: str
    livekit_url: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Joyce server starting...")
    print(f"🔗 LiveKit URL: {env.LIVEKIT_URL}")
    yield
    print("👋 Joyce server shutting down...")


app = FastAPI(
    title="Joyce Server",
    description="Health and wellbeing voice assistant server",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "message": "Joyce server is running",
        "version": "1.0.0",
        "livekit_configured": bool(env.LIVEKIT_API_KEY and env.LIVEKIT_API_SECRET),
    }


@app.post("/api/token")
async def create_token(request: TokenRequest) -> TokenResponse:
    """Create a LiveKit access token for joining a room."""
    if not env.LIVEKIT_API_KEY or not env.LIVEKIT_API_SECRET:
        raise HTTPException(
            status_code=500,
            detail="LiveKit credentials not configured. Please set LIVEKIT_API_KEY and LIVEKIT_API_SECRET environment variables.",
        )

    try:
        # Create access token using the modern LiveKit API pattern
        jwt_token = (
            api.AccessToken(env.LIVEKIT_API_KEY, env.LIVEKIT_API_SECRET)
            .with_identity(request.participant_name)
            .with_name(request.participant_name)
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=request.room_name,
                    # Allow the participant to publish audio/video
                    can_publish=True,
                    can_subscribe=True,
                    can_publish_data=True,
                )
            )
            .to_jwt()
        )

        return TokenResponse(
            token=jwt_token,
            room_name=request.room_name,
            livekit_url=env.LIVEKIT_URL or "wss://localhost:7880",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create token: {e!s}",
        ) from e


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """Detailed health check with LiveKit connection status."""
    livekit_configured = bool(env.LIVEKIT_API_KEY and env.LIVEKIT_API_SECRET)

    return {
        "status": "healthy",
        "livekit": {
            "configured": livekit_configured,
            "url": env.LIVEKIT_URL,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "joyce.server:app",
        host="127.0.0.1",  # Bind to localhost only for security
        port=env.PORT,
        reload=True,
        log_level="info",
    )
