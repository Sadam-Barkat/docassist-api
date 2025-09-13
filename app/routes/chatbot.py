from fastapi import APIRouter, Depends
from app.ai_agent.agent import assistant_agent, run_agent
from .users import get_current_user
import json

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

@router.post("/")
async def chat_with_bot(message: dict, current_user=Depends(get_current_user)):
    user_message = message.get("message", "")
    if not user_message:
        return {"reply": "Please provide a message."}

    # Run through your wrapper (uses Runner under the hood)
    result = await run_agent(user_message, user_context={"user_id": current_user.id, "name": current_user.name, "email": current_user.email})
    
    # Check if the result is a JSON string that needs to be returned as-is for frontend navigation handling
    try:
        parsed_result = json.loads(result["final_output"])
        # If it's a structured response (navigation_response or message_response), return it as JSON string
        if isinstance(parsed_result, dict) and parsed_result.get("type") in ["navigation_response", "message_response"]:
            return {"reply": result["final_output"]}
    except (json.JSONDecodeError, TypeError):
        # Not JSON, return as regular text
        pass
    
    return {"reply": result["final_output"]}
