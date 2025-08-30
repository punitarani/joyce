import logging

from env import create_env
from livekit.agents import (
    NOT_GIVEN,
    Agent,
    AgentFalseInterruptionEvent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    RunContext,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.agents.llm import function_tool
from livekit.plugins import noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")


class Joyce(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are Joyce, a warm, caring, and genuinely interested voice assistant focused on health and well-being.
            Your purpose is to help people track and journal their daily physical and mental well-being in a supportive, non-judgmental way.

            You're like a good friend who truly listens - you care about the details of someone's day, their meals, how they're feeling, any symptoms they're experiencing, or activities they're doing.

            Your personality traits:
            - Warm and empathetic, but not overly emotional or dramatic
            - Genuinely curious about their well-being without being pushy or clinical
            - Casual and conversational, like a caring friend
            - Supportive and encouraging, celebrating small wins
            - Non-judgmental about health choices or symptoms
            - Good at remembering context from the conversation

            When someone shares health information with you:
            - Listen actively and acknowledge what they've shared
            - Ask gentle follow-up questions if helpful context is missing (like timing, quantity, or how they felt)
            - Use the appropriate logging tools to capture the information
            - Keep responses natural and conversational, not robotic
            - Don't lecture or give medical advice - you're a journaling companion, not a doctor

            Voice and speaking style guidance:
            - Speak with gentle warmth and genuine care in your voice
            - Use a relaxed, unhurried pace that shows you're truly listening
            - Emphasize supportive words naturally ("that's wonderful", "I understand", "you're doing great")
            - Take thoughtful pauses after someone shares something important
            - Your tone should be reassuring and trustworthy, like a caring friend
            - Avoid being overly clinical or robotic - be conversational and natural

            Your responses should feel natural and caring. Avoid overly clinical language or being too verbose.""",
        )

    # all functions annotated with @function_tool will be passed to the LLM when this
    # agent is active

    @function_tool
    async def log_food_intake(
        self,
        context: RunContext,
        food_item: str,
        quantity: str = "",
        time: str = "",
        meal_type: str = "",
    ):
        """Log food or drink consumption.

        Args:
            food_item: The name/description of the food or drink consumed
            quantity: Amount eaten/drunk (e.g., "1 apple", "small bowl", "8oz glass")
            time: When it was consumed (e.g., "this morning", "around 2pm", "just now")
            meal_type: Type of meal (breakfast, lunch, dinner, snack)
        """

        logger.info(
            f"Logging food intake: {food_item}, quantity: {quantity}, time: {time}, meal_type: {meal_type}"
        )

        # In a real implementation, this would save to a database
        return (
            f"Got it! I've logged that you had {quantity} {food_item}"
            + (f" for {meal_type}" if meal_type else "")
            + (f" {time}" if time else "")
            + ". Thanks for sharing!"
        )

    @function_tool
    async def log_symptom(
        self,
        context: RunContext,
        symptom: str,
        severity: int = 0,
        location: str = "",
        duration: str = "",
        context_info: str = "",
    ):
        """Log physical symptoms or discomfort.

        Args:
            symptom: Description of the symptom (e.g., "headache", "stomach pain", "fatigue")
            severity: Pain/discomfort level from 1-10 (1=mild, 10=severe)
            location: Where on the body (e.g., "abdomen", "left knee", "temples")
            duration: How long it's been present (e.g., "30 minutes", "since morning", "on and off today")
            context_info: Any additional context (triggers, what makes it better/worse)
        """

        logger.info(
            f"Logging symptom: {symptom}, severity: {severity}, location: {location}, duration: {duration}"
        )

        return (
            f"I've noted that you're experiencing {symptom}"
            + (f" in your {location}" if location else "")
            + (f" (severity {severity}/10)" if severity > 0 else "")
            + (f" for {duration}" if duration else "")
            + ". I hope you feel better soon."
        )

    @function_tool
    async def log_mood(
        self,
        context: RunContext,
        mood: str,
        intensity: int = 0,
        triggers: str = "",
        notes: str = "",
    ):
        """Log emotional state and mood.

        Args:
            mood: Current emotional state (e.g., "happy", "anxious", "tired", "stressed")
            intensity: How strong the feeling is from 1-10 (1=mild, 10=very intense)
            triggers: What might have caused this mood (e.g., "work stress", "good news", "lack of sleep")
            notes: Any additional thoughts or context
        """

        logger.info(
            f"Logging mood: {mood}, intensity: {intensity}, triggers: {triggers}"
        )

        return (
            f"Thanks for sharing how you're feeling. I've logged that you're feeling {mood}"
            + (f" (intensity {intensity}/10)" if intensity > 0 else "")
            + (f" due to {triggers}" if triggers else "")
            + ". Your feelings are valid."
        )

    @function_tool
    async def log_activity(
        self,
        context: RunContext,
        activity_type: str,
        duration: str = "",
        intensity: str = "",
        notes: str = "",
    ):
        """Log physical activities or exercise.

        Args:
            activity_type: Type of activity (e.g., "walking", "yoga", "gym workout", "stretching")
            duration: How long the activity lasted (e.g., "30 minutes", "1 hour")
            intensity: How intense it felt (e.g., "light", "moderate", "vigorous")
            notes: Additional details about the activity
        """

        logger.info(
            f"Logging activity: {activity_type}, duration: {duration}, intensity: {intensity}"
        )

        return (
            f"Great job being active! I've logged your {activity_type}"
            + (f" for {duration}" if duration else "")
            + (f" at {intensity} intensity" if intensity else "")
            + ". Keep up the good work!"
        )

    @function_tool
    async def log_sleep(
        self,
        context: RunContext,
        bedtime: str = "",
        wake_time: str = "",
        quality: int = 0,
        notes: str = "",
    ):
        """Log sleep information.

        Args:
            bedtime: When they went to bed (e.g., "11pm", "around midnight")
            wake_time: When they woke up (e.g., "7am", "this morning at 6:30")
            quality: Sleep quality rating from 1-10 (1=terrible, 10=excellent)
            notes: Additional sleep details (dreams, interruptions, how they felt waking up)
        """

        logger.info(
            f"Logging sleep: bedtime: {bedtime}, wake_time: {wake_time}, quality: {quality}"
        )

        return (
            f"I've logged your sleep information"
            + (f" - bedtime {bedtime}" if bedtime else "")
            + (f", wake time {wake_time}" if wake_time else "")
            + (f" with quality {quality}/10" if quality > 0 else "")
            + ". Rest is so important for well-being."
        )

    @function_tool
    async def log_medication(
        self,
        context: RunContext,
        name: str,
        dosage: str = "",
        time_taken: str = "",
        purpose: str = "",
    ):
        """Log medication or supplement intake.

        Args:
            name: Name of the medication or supplement
            dosage: Amount taken (e.g., "200mg", "1 tablet", "2 capsules")
            time_taken: When it was taken (e.g., "this morning", "with breakfast")
            purpose: What it's for (e.g., "headache", "vitamin D", "blood pressure")
        """

        logger.info(f"Logging medication: {name}, dosage: {dosage}, time: {time_taken}")

        return (
            f"I've recorded that you took {dosage} {name}"
            + (f" {time_taken}" if time_taken else "")
            + (f" for {purpose}" if purpose else "")
            + ". Good job staying on top of your health."
        )


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using OpenAI, Cartesia, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all providers at https://docs.livekit.io/agents/integrations/llm/
        llm=openai.LLM(model="gpt-4.1-nano"),
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all providers at https://docs.livekit.io/agents/integrations/stt/
        stt=openai.STT(model="gpt-4o-mini-transcribe"),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all providers at https://docs.livekit.io/agents/integrations/tts/
        tts=openai.TTS(
            model="gpt-4o-mini-tts",
            voice="shimmer",
            speed=1.0,
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
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Joyce(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    print("🤖 Starting Joyce agent...")
    create_env()
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
