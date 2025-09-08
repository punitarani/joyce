import json
import logging

from livekit.agents import (
    NOT_GIVEN,
    AgentFalseInterruptionEvent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    metrics,
)
from livekit.plugins import (
    assemblyai,
    cartesia,
    google,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from joyce.services.user.user_service import UserService

from .joyce import JoyceAgent
from .onboarding import OnboardingAgent
from .user import UserData, get_user_profile

logger = logging.getLogger("agent")


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def select_agent(user_id: str):
    """
    Select the appropriate agent based on user onboarding status.

    Args:
        user_id: User ID to check onboarding status for

    Returns:
        OnboardingAgent if user needs onboarding, JoyceAgent otherwise
    """
    user_profile = await get_user_profile(user_id)

    userdata = UserData(user_id=user_id, user_profile=user_profile)

    # Onboard: If user does not have a profile or is not onboarded
    if not user_profile or not user_profile.is_onboarding_complete:
        return OnboardingAgent(userdata=userdata)

    # Joyce: If user has a fully onboarded profile
    return JoyceAgent(userdata=userdata)


async def entrypoint(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Get user data
    metadata = {}
    if ctx.job.metadata:
        if isinstance(ctx.job.metadata, str):
            metadata = json.loads(ctx.job.metadata)
        elif isinstance(ctx.job.metadata, dict):
            metadata = ctx.job.metadata
    user_id = metadata.get("user_id")

    await ctx.connect()

    # If the job is from a call, set the user id from the SIP caller id
    participant = await ctx.wait_for_participant()
    if participant:
        phone_number = participant.attributes.get("sip.phoneNumber")
        if phone_number:
            user_id = await UserService.get_or_create(phone_number=phone_number)

    if not user_id:
        raise ValueError("User ID is required")

    # Determine which agent to use based on user profile status
    agent = await select_agent(user_id)

    # Set up a voice AI pipeline using OpenAI, Cartesia, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all providers at https://docs.livekit.io/agents/integrations/llm/
        llm=google.LLM(
            model="gemini-2.5-flash-lite",
        ),
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all providers at https://docs.livekit.io/agents/integrations/stt/
        stt=assemblyai.STT(),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all providers at https://docs.livekit.io/agents/integrations/tts/
        tts=cartesia.TTS(
            model="sonic-turbo",
            voice="6f84f4b8-58a2-430c-8c79-688dad597532",
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # sometimes background noise could interrupt the agent session, these are considered false positive interruptions
    # when it's detected, you may resume the agent's speech
    @session.on("agent_false_interruption")
    def _on_agent_false_interruption(ev: AgentFalseInterruptionEvent):
        logger.info("false positive interruption, resuming")
        session.generate_reply(instructions=ev.extra_instructions or NOT_GIVEN)

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info("Usage: %s", summary)

    ctx.add_shutdown_callback(log_usage)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVCTelephony(),
            close_on_disconnect=True,
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()
