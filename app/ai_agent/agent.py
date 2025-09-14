# backend/app/ai_agent/agent.py
from openai import AsyncOpenAI
import asyncio
from typing import Any
from agents import Agent, Runner, SQLiteSession, OpenAIChatCompletionsModel, set_default_openai_key
from .prompts import SYSTEM_INSTRUCTIONS
from .tools import (
    show_dashboard, show_admin_dashboard, show_doctors, show_appointments, 
    show_profile, book_appointment, start_booking, show_users, delete_user, 
    edit_user, update_user_profile, add_doctor, delete_doctor, edit_doctor
)
from dotenv import load_dotenv
import os

load_dotenv()

# --- Set the OpenAI API key properly ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Ensure your .env has OPENAI_API_KEY
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment")
set_default_openai_key(OPENAI_API_KEY)

# Create the main assistant agent. Keep instructions clear and focused.
assistant_agent = Agent(
    name="DocAssist",
    instructions=SYSTEM_INSTRUCTIONS,
    tools=[
        show_dashboard, show_admin_dashboard, show_doctors, show_appointments,
        show_profile, book_appointment, start_booking, show_users,
        delete_user, edit_user, update_user_profile, add_doctor,
        delete_doctor, edit_doctor
    ]
)

# --- Add a session store ---
_session_store: dict[str, SQLiteSession] = {}

def get_or_create_session(user_id: str | None = None) -> SQLiteSession:
    """Return the existing session for a user, or create a new one if none exists."""
    if not user_id:
        return SQLiteSession(session_id="anonymous")  # fallback session
    if user_id not in _session_store:
        _session_store[user_id] = SQLiteSession(session_id=user_id)
    return _session_store[user_id]


async def run_agent(user_input: str, user_context: dict | None = None, max_turns: int = 10) -> dict[str, Any]:
    """
    Run the DocAssist agent with a user input and optional context.
    Returns dict with shape {'final_output': str, 'raw': run_result}
    """
    try:
        user_id = str(user_context.get("user_id")) if user_context and "user_id" in user_context else None
        user_session = get_or_create_session(user_id)

        # Enhanced context with debugging
        enhanced_context = user_context or {}
        print(f"Running agent with input: {user_input}")
        print(f"Context: {enhanced_context}")

        run_result = await Runner.run(
            assistant_agent,
            input=user_input,
            max_turns=max_turns,
            context=enhanced_context,
            session=user_session
        )
        
        print(f"Agent run completed. Final output: {run_result.final_output}")
        
        return {"final_output": run_result.final_output, "raw": run_result}
    except Exception as e:
        print(f"Error in run_agent: {str(e)}")
        return {"final_output": f"Agent error: {str(e)}", "raw": None}
