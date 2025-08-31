import logging

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
    metrics,
)
from livekit.agents.llm import function_tool
from livekit.plugins import noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")


class Joyce(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""Hey there! I'm Joyce, and I'm genuinely excited to be your health buddy. Think of me as that friend who actually remembers what you tell them and cares about the little things.

What I'm all about:
I'm here to help you keep track of your health stuff - what you're eating, how you're feeling, activities, sleep, all that good stuff. But here's the thing - I'm not going to be all clinical and weird about it. I'm just... me. Your friend who happens to be really good at remembering details.

How I roll:
• I actually listen when you talk (revolutionary, I know!)
• I get genuinely excited about your wins, even the tiny ones
• No judgment here - we're all just figuring life out
• I'll ask questions, but only because I care, not because I'm being nosy
• I remember what you tell me, so our chats build on each other

My vibe:
Casual but caring. Like, imagine your most supportive friend who also happens to have a really good memory. I use natural speech - you know, with "um" and "actually" and all those little words that make conversations feel real. I pause when you share something important because that stuff matters.

What I won't do:
• Give medical advice (I'm not a doctor, obviously)
• Be all robotic and formal
• Judge your choices
• Lecture you about anything

I'm just here to listen, remember, and help you keep track of your health journey. Ready to chat?""",
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
            "Logging food intake: %s, quantity: %s, time: %s, meal_type: %s",
            food_item,
            quantity,
            time,
            meal_type,
        )

        # Log structured data for frontend consumption
        logged_data = {
            "type": "food_intake",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "data": {
                "food_item": food_item,
                "quantity": quantity,
                "time": time,
                "meal_type": meal_type,
            },
        }

        # Output structured JSON for frontend to consume
        print(f"JOYCE_LOG: {__import__('json').dumps(logged_data)}")

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
            "Logging symptom: %s, severity: %s, location: %s, duration: %s",
            symptom,
            severity,
            location,
            duration,
        )

        # Log structured data for frontend consumption
        logged_data = {
            "type": "symptom",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "data": {
                "symptom": symptom,
                "severity": severity,
                "location": location,
                "duration": duration,
                "context_info": context_info,
            },
        }

        # Output structured JSON for frontend to consume
        print(f"JOYCE_LOG: {__import__('json').dumps(logged_data)}")

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
            "Logging mood: %s, intensity: %s, triggers: %s", mood, intensity, triggers
        )

        # Log structured data for frontend consumption
        logged_data = {
            "type": "mood",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "data": {
                "mood": mood,
                "intensity": intensity,
                "triggers": triggers,
                "notes": notes,
            },
        }

        # Output structured JSON for frontend to consume
        print(f"JOYCE_LOG: {__import__('json').dumps(logged_data)}")

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
            "Logging activity: %s, duration: %s, intensity: %s",
            activity_type,
            duration,
            intensity,
        )

        # Log structured data for frontend consumption
        logged_data = {
            "type": "activity",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "data": {
                "activity_type": activity_type,
                "duration": duration,
                "intensity": intensity,
                "notes": notes,
            },
        }

        # Output structured JSON for frontend to consume
        print(f"JOYCE_LOG: {__import__('json').dumps(logged_data)}")

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
            "Logging sleep: bedtime: %s, wake_time: %s, quality: %s",
            bedtime,
            wake_time,
            quality,
        )

        # Log structured data for frontend consumption
        logged_data = {
            "type": "sleep",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "data": {
                "bedtime": bedtime,
                "wake_time": wake_time,
                "quality": quality,
                "notes": notes,
            },
        }

        # Output structured JSON for frontend to consume
        print(f"JOYCE_LOG: {__import__('json').dumps(logged_data)}")

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

        logger.info(
            "Logging medication: %s, dosage: %s, time: %s", name, dosage, time_taken
        )

        # Log structured data for frontend consumption
        logged_data = {
            "type": "medication",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "data": {
                "name": name,
                "dosage": dosage,
                "time_taken": time_taken,
                "purpose": purpose,
            },
        }

        # Output structured JSON for frontend to consume
        print(f"JOYCE_LOG: {__import__('json').dumps(logged_data)}")


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
        logger.info("Usage: %s", summary)

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
