import logging
import re
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from sqlalchemy.orm import Session, joinedload

from agent.llm_agent import AssistantError, run_shopping_assistant
from crud.crud import create_message
from database import get_db
from models.models import Message
from models.models import User as UserModel
from schemas.schemas import AskRequest, MessageCreate, ResMessage
from security import ensure_cart_member, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])

# How much of the conversation to replay to the model. Older turns add tokens
# and stale suggestions without improving the reply.
MAX_HISTORY_MESSAGES = 12

# Assistant rows written before the tool-calling rewrite can carry a fenced
# JSON block and a "Cart Updates:" trailer. Feeding those back teaches the
# model to emit them again, so strip them on the way in.
_CODE_BLOCK_RE = re.compile(r"```(?:json)?.*?```", re.DOTALL)
_CART_UPDATES_RE = re.compile(r"\n*Cart Updates:\n(?:[•\-*].*(?:\n|$))+")


def _clean_assistant_text(text: str) -> str:
    text = _CODE_BLOCK_RE.sub("", text or "")
    text = _CART_UPDATES_RE.sub("", text)
    return text.strip()


def _build_history(db: Session, cart_id: int) -> List[BaseMessage]:
    """Load the tail of the conversation as typed chat messages."""
    rows = (
        db.query(Message)
        .options(joinedload(Message.sender))
        .filter(Message.cart_id == cart_id)
        .order_by(Message.timestamp.desc(), Message.message_id.desc())
        .limit(MAX_HISTORY_MESSAGES)
        .all()
    )
    rows.reverse()

    history: List[BaseMessage] = []
    for row in rows:
        if row.sender_type == "assistant":
            content = _clean_assistant_text(row.message_content)
            if content:
                history.append(AIMessage(content=content))
        else:
            content = (row.message_content or "").strip()
            if content:
                # Several people share a cart, so name who is speaking.
                speaker = row.sender.user_name if row.sender else None
                history.append(
                    HumanMessage(
                        content=f"{speaker}: {content}" if speaker else content
                    )
                )
    return history


@router.post("/ask")
def ask_assistant(
    request: AskRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Store the user's message, let the assistant act on the cart, and reply.

    The sender is the token holder, not a body field, and membership of the
    cart is checked first. The assistant then reaches the cart only through
    tools bound to that cart and user.
    """
    ensure_cart_member(db, request.cart_id, current_user)

    user_msg = MessageCreate(
        cart_id=request.cart_id,
        sender_id=current_user.user_id,
        sender_type="user",
        message_content=request.message,
    )
    create_message(db, user_msg)

    history = _build_history(db, request.cart_id)

    try:
        reply, mutation_log = run_shopping_assistant(
            db=db,
            cart_id=request.cart_id,
            user_id=current_user.user_id,
            history=history,
        )
    except AssistantError as exc:
        # The model or its provider failed. The cause is already logged; only
        # the vetted message reaches the client.
        logger.warning(
            "Assistant unavailable (cart_id=%s): %s",
            request.cart_id,
            exc.user_message,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.user_message,
        ) from exc
    except Exception as exc:
        logger.exception(
            "Unexpected assistant failure (cart_id=%s, user_id=%s)",
            request.cart_id,
            current_user.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong handling that message.",
        ) from exc

    # sender_id stays NULL: the assistant is not one of the cart's users.
    create_message(
        db,
        MessageCreate(
            cart_id=request.cart_id,
            sender_id=None,
            sender_type="assistant",
            message_content=reply,
        ),
    )

    return {
        "cart_id": request.cart_id,
        "user_message": request.message,
        "assistant_response": reply,
        "items_added": mutation_log.items_added,
        "cart_changed": mutation_log.cart_changed,
    }


@router.get("/{cart_id}", response_model=List[ResMessage])
def get_messages(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Fetch all messages for a given cart, including sender username.
    """
    ensure_cart_member(db, cart_id, current_user)

    # Fetch messages and eager-load the sender relationship
    messages = (
        db.query(Message)
        .options(joinedload(Message.sender))
        .filter(Message.cart_id == cart_id)
        .order_by(Message.timestamp.asc())
        .all()
    )

    result = []
    for msg in messages:
        result.append(
            ResMessage(
                message_id=msg.message_id,
                cart_id=msg.cart_id,
                sender_id=msg.sender_id,
                sender_type=msg.sender_type,
                sender_name=(
                    msg.sender.user_name
                    if msg.sender
                    else ("Assistant" if msg.sender_type == "assistant" else None)
                ),
                message_content=msg.message_content,
                timestamp=msg.timestamp,
            )
        )

    return result
