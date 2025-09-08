from livekit.agents import RunContext

from joyce.agent.user import UserData
from joyce.db.schema import UserProfile


def get_user_id_from_context(context: RunContext[UserData]) -> str:
    return context.userdata.user_id


async def get_user_profile_from_context(context: RunContext[UserData]) -> UserProfile:
    return await context.userdata.get_user_profile()
