import asyncio

from livekit.agents import RunContext, function_tool

from joyce.agent.user import UserData


@function_tool()
async def goodbye_and_end_call(context: RunContext[UserData]) -> None:
    """
    Say goodbye to the user and end the call.
    """
    await context.session.generate_reply(instructions="Say goodbye to the user")
    context._close_session_task = asyncio.create_task(context.session.aclose())
