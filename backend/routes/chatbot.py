from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth.dependencies import require_roles
from backend.chatbot import service as llm
from backend.chatbot.sql_generator import answer_question

router = APIRouter(tags=["chatbot"])


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)


@router.post("/chat")
def chat(body: ChatRequest, _user=Depends(require_roles("manager", "employee"))):
    if not llm.llm_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "Chatbot is not configured. Set LLM_API_KEY (and LLM_PROVIDER/LLM_MODEL) "
                "in the backend environment. This prototype does not return fake answers."
            ),
        )
    try:
        return answer_question(body.question)
    except llm.LLMNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM or SQL step failed: {exc}") from exc
