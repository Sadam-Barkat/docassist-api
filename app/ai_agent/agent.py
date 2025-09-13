# backend/app/ai_agent/agent.py
import asyncio
from typing import Any
from agents import Agent, Runner, SQLiteSession
from .prompts import SYSTEM_INSTRUCTIONS
from .tools import (
    show_dashboard, show_admin_dashboard, show_doctors, show_appointments, 
    show_profile, start_booking, book_appointment, show_users, delete_user, 
    edit_user, update_user_profile, add_doctor, delete_doctor, edit_doctor
)
from dotenv import load_dotenv
import os

load_dotenv()

# Create the main assistant agent. Keep instructions clear and focused.
assistant_agent = Agent(
    name="DocAssist",
    instructions=SYSTEM_INSTRUCTIONS,
    tools=[
        show_dashboard, show_admin_dashboard, show_doctors, show_appointments,
        show_profile, start_booking, book_appointment, show_users,
        delete_user, edit_user, update_user_profile, add_doctor,
        delete_doctor, edit_doctor
    ],
    model="gemini-1.5-flash",  
    api_key=os.getenv("GEMINI_API_KEY"), 
    provider="google"  
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


async def run_agent(user_input: str, user_context: dict | None = None, max_turns: int = 5) -> dict[str, Any]:
    """
    Run the DocAssist agent with a user input and optional context.
    - user_input: text from the user
    - user_context: optional context dict (e.g., {'user_id': 123})
    Returns:
      dict with shape {'final_output': str, 'trace': run_result}
    """
    user_id = str(user_context.get("user_id")) if user_context and "user_id" in user_context else None
    user_session = get_or_create_session(user_id)

    run_result = await Runner.run(
        assistant_agent,
        input=user_input,
        max_turns=max_turns,
        context=user_context or {},
        session=user_session
    )
    # run_result has fields like final_output, new_items, etc.
    return {"final_output": run_result.final_output, "raw": run_result}

