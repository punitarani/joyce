from __future__ import annotations

import os
import pathlib
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


class Environment(BaseModel):
    """Environment variables configuration with validation and type parsing."""

    # Server Configuration
    PORT: int = Field(default=3000, description="Server port")
    NODE_ENV: str = Field(default="development", description="Node environment")

    # App URLs
    API_URL: str = Field(default="http://localhost:3000", description="Backend API URL")

    # LiveKit Configuration
    LIVEKIT_URL: Optional[str] = Field(default=None, description="LiveKit server URL")
    LIVEKIT_API_KEY: Optional[str] = Field(default=None, description="LiveKit API key")
    LIVEKIT_API_SECRET: Optional[str] = Field(
        default=None, description="LiveKit API secret"
    )

    # Supabase Configuration
    SUPABASE_URL: Optional[str] = Field(default=None, description="Supabase URL")
    SUPABASE_SECRET_KEY: Optional[str] = Field(
        default=None, description="Supabase secret key"
    )
    SUPABASE_PUBLISHABLE_KEY: Optional[str] = Field(
        default=None, description="Supabase publishable key"
    )

    # AssemblyAI Configuration
    ASSEMBLYAI_API_KEY: Optional[str] = Field(
        default=None, description="AssemblyAI API key"
    )

    # Cartesia Configuration
    CARTESIA_API_KEY: Optional[str] = Field(
        default=None, description="Cartesia API key"
    )

    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")

    # Database Configuration
    DB_URL: Optional[str] = Field(default=None, description="Database URL")

    # ChromaDB Configuration
    CHROMA_API_KEY: Optional[str] = Field(default=None, description="ChromaDB API key")
    CHROMA_TENANT: Optional[str] = Field(default=None, description="ChromaDB tenant")
    CHROMA_DATABASE: Optional[str] = Field(
        default=None, description="ChromaDB database"
    )

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }

    @field_validator("NODE_ENV")
    @classmethod
    def validate_node_env(cls, v):
        """Validate NODE_ENV is one of expected values."""
        valid_envs = ["development", "production", "test"]
        if v not in valid_envs:
            raise ValueError(f"NODE_ENV must be one of {valid_envs}")
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.NODE_ENV == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.NODE_ENV == "production"


def create_env() -> Environment:
    """Create and validate environment configuration."""
    try:
        # Path of the server app
        server_dir = pathlib.Path(__file__).parents[1].resolve()
        project_dir = server_dir.parents[1].resolve()

        env_path = project_dir.joinpath(".env")

        print(f"Loading environment from {env_path}")
        load_dotenv(env_path, verbose=True)

        return Environment(
            PORT=int(os.getenv("PORT", "3000")),
            NODE_ENV=os.getenv("NODE_ENV", "development"),
            API_URL=os.getenv("API_URL", "http://localhost:3000"),
            DB_URL=os.getenv("DB_URL"),
            CHROMA_API_KEY=os.getenv("CHROMA_API_KEY"),
            CHROMA_TENANT=os.getenv("CHROMA_TENANT"),
            CHROMA_DATABASE=os.getenv("CHROMA_DATABASE"),
            ASSEMBLYAI_API_KEY=os.getenv("ASSEMBLYAI_API_KEY"),
            CARTESIA_API_KEY=os.getenv("CARTESIA_API_KEY"),
            LIVEKIT_URL=os.getenv("LIVEKIT_URL"),
            LIVEKIT_API_KEY=os.getenv("LIVEKIT_API_KEY"),
            LIVEKIT_API_SECRET=os.getenv("LIVEKIT_API_SECRET"),
            SUPABASE_URL=os.getenv("SUPABASE_URL"),
            SUPABASE_SECRET_KEY=os.getenv("SUPABASE_SECRET_KEY"),
            SUPABASE_PUBLISHABLE_KEY=os.getenv("SUPABASE_PUBLISHABLE_KEY"),
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
        )
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        raise


env = create_env()

print(f"✅ Environment loaded successfully ({env.NODE_ENV} mode)")
