from livekit.agents import RunContext, function_tool

from joyce.agent.functions.onboarding import (
    evaluate_onboarding_readiness,
    mark_user_onboarding_complete,
)
from joyce.agent.user import UserData

from .utils import get_user_id_from_context


@function_tool()
async def review_and_complete_onboarding(context: RunContext[UserData]) -> str:
    """
    Review user's onboarding progress and complete if ready, or provide recommendations.

    This function evaluates if the user has provided enough information to start
    using Joyce effectively. If ready, marks onboarding as complete. Otherwise,
    provides specific recommendations on what information is still needed.

    Example:
    ```json
    {}
    ```
    """
    user_id = get_user_id_from_context(context)

    # Evaluate onboarding readiness using core function
    assessment = await evaluate_onboarding_readiness(user_id)

    if assessment["is_ready"]:
        # Mark onboarding as complete
        success = await mark_user_onboarding_complete(user_id)
        if success:
            return "Onboarding completed successfully! I have enough information to start providing personalized support. Let's get started with using Joyce!"
        return "Your onboarding appears complete, but there was an issue updating your status. Please try again."
    # Provide specific recommendations
    missing = assessment.get("missing_critical", [])
    recommendations = assessment.get("recommendations", [])
    reasoning = assessment.get("reasoning", "")
    confidence = assessment.get("confidence", 0.0)

    response = f"I need a bit more information before we can complete your onboarding (confidence: {confidence:.1%})."

    if missing:
        response += f"\n\nMissing critical items: {', '.join(missing)}"

    if recommendations:
        response += "\n\nHere's what would help:\n" + "\n".join(
            f"- {rec}" for rec in recommendations
        )

    if reasoning:
        response += f"\n\nReasoning: {reasoning}"

    response += "\n\nFeel free to share more about yourself, and I'll check again when you're ready!"

    return response
