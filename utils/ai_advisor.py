# utils/ai_advisor.py

from groq import Groq

client = Groq(
    api_key="GROQ_API_KEY"  # Replace with your actual API key
)

def generate_enforcement_plan(
    station,
    risk_score,
    priority,
    officers,
    patrol_window,
    reduction,
    hotspots
):

    prompt = f"""
    You are a Bengaluru Traffic Enforcement Expert.

    Police Station: {station}
    Risk Score: {risk_score}
    Priority: {priority}
    Officers: {officers}
    Patrol Window: {patrol_window}
    Expected Reduction: {reduction}%

    Hotspots:
    {hotspots}

    Generate a professional enforcement strategy.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4
    )

    return response.choices[0].message.content