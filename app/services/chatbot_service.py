# backend/app/services/chatbot_service.py
from typing import Dict
from app.ai_agent.agent import run_agent_sync


def handle_chat_message(user_id: int, message: str) -> Dict:
    """
    Handle a chat message from frontend and return agent response.
    """
    context = {"user_id": user_id}
    result = run_agent_sync(message, user_context=context)
    return {"reply": result["final_output"]}
