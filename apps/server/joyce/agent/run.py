from livekit.agents import (
    WorkerOptions,
    cli,
)

from joyce.env import create_env

from .voice import entrypoint, prewarm

if __name__ == "__main__":
    print("🤖 Starting Joyce agent...")
    create_env()
    cli.run_app(
        WorkerOptions(
            agent_name="joyce_agent",
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )
