# agent/llm_agent.py
"""Gemini-backed shopping assistant.

Uses native function calling (via LangGraph's prebuilt tool-calling agent)
rather than a text ReAct loop, so tool arguments arrive as typed JSON and cart
writes happen through tools instead of being regexed out of the reply.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from sqlalchemy.orm import Session

from agent.prompt_templates import (
    CONTEXT_TEMPLATE,
    SYSTEM_PROMPT,
    UNDONE_CHANGE_NUDGE,
)
from agent.tools import CartMutationLog, build_tools

load_dotenv()

logger = logging.getLogger(__name__)

# Gemini 3.x models require thought signatures on function calls, which
# langchain-google-genai 2.x does not send; moving past 2.5 means upgrading the
# langchain/langgraph stack first.
# Override with GEMINI_MODEL in .env, e.g. to move to a model with a separate
# free-tier quota.
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
# Low temperature: this is tool selection and budget arithmetic, not prose.
TEMPERATURE = 0.1
# Wall-clock limit for a single Gemini call.
REQUEST_TIMEOUT_SECONDS = 30
# Each tool round trip costs two graph steps, so this allows ~9 rounds (cart
# summary, a few searches, a retry, the add) before the agent is cut off
# rather than looping until it exhausts the quota.
RECURSION_LIMIT = 20

# Phrases that report a cart change as done ("I've added", "I removed").
# Offers like "I can add..." deliberately do not match.
_CLAIMS_CHANGE_RE = re.compile(
    r"\b(i\s*(?:'ve|have)?\s*(?:added|put|included|updated|changed|increased|"
    r"decreased|removed|swapped|replaced)|(?:has|have) been (?:added|updated|"
    r"removed))\b",
    re.IGNORECASE,
)

_UNDONE_CHANGE_FALLBACK = (
    "Sorry, I was not able to change the cart for that. Could you try asking "
    "again, perhaps naming the items you want?"
)

_GENERIC_FAILURE = (
    "Sorry, I could not work on the cart just now. Please try again in a moment."
)


class AssistantError(Exception):
    """Raised when the assistant cannot produce a reply.

    `user_message` is safe to show to the user; the underlying cause is logged
    rather than returned, so internals never leak into the chat.
    """

    def __init__(self, user_message: str, cause: Optional[BaseException] = None):
        super().__init__(user_message)
        self.user_message = user_message
        self.cause = cause


def _build_llm() -> ChatGoogleGenerativeAI:
    if not os.getenv("GOOGLE_API_KEY"):
        raise AssistantError(
            "The shopping assistant is not configured yet, so I cannot help with "
            "the cart right now."
        )
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        timeout=REQUEST_TIMEOUT_SECONDS,
        max_retries=2,
    )


# The model client is stateless and safe to share; the agent graph is rebuilt
# per request because its tools are bound to that request's cart and user.
try:
    _llm: Optional[ChatGoogleGenerativeAI] = _build_llm()
except AssistantError as exc:
    logger.warning("Gemini client unavailable at import: %s", exc.user_message)
    _llm = None


def _message_text(message: BaseMessage) -> str:
    """Flatten message content, which Gemini may return as a list of parts."""
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and isinstance(part.get("text"), str):
                parts.append(part["text"])
        return " ".join(parts).strip()
    return str(content).strip()


def _classify(exc: BaseException) -> str:
    """Map a failure to a message worth showing the user."""
    name = type(exc).__name__
    text = str(exc).lower()

    if name == "GraphRecursionError":
        return (
            "That turned out to be more involved than I could work through in "
            "one go. Could you narrow it down a little?"
        )
    if "resourceexhausted" in name.lower() or "quota" in text or "rate limit" in text:
        return (
            "I have hit my usage limit for the moment. Please try again shortly."
        )
    if "deadline" in name.lower() or "timeout" in name.lower() or "timed out" in text:
        return "That took too long to work out. Could you try again?"
    if (
        "permissiondenied" in name.lower()
        or "unauthenticated" in name.lower()
        or "api key" in text
    ):
        return (
            "The shopping assistant is not configured correctly, so I cannot "
            "help with the cart right now."
        )
    return _GENERIC_FAILURE


def run_shopping_assistant(
    db: Session,
    cart_id: int,
    user_id: int,
    history: list[BaseMessage],
) -> tuple[str, CartMutationLog]:
    """Answer the latest message in `history` and act on the cart.

    `cart_id` and `user_id` are bound into the tools and never shown to the
    model. Returns the assistant's reply and a log of what it changed.
    """
    if _llm is None:
        raise AssistantError(
            "The shopping assistant is not configured yet, so I cannot help "
            "with the cart right now."
        )
    if not history:
        raise AssistantError("There was no message for me to reply to.")

    tools, mutation_log = build_tools(db=db, cart_id=cart_id, user_id=user_id)
    agent = create_react_agent(_llm, tools)

    # Run the two read-only lookups the model needs on every turn here, so
    # they cost no model requests.
    by_name = {tool.name: tool for tool in tools}
    context = CONTEXT_TEMPLATE.format(
        cart_summary=by_name["get_cart_summary"].func(),
        categories=by_name["get_categories"].func(),
    )

    # The system prompt is prepended to the message list rather than passed as
    # a constructor argument, whose name has moved between LangGraph versions.
    messages: list[BaseMessage] = [
        SystemMessage(content=SYSTEM_PROMPT + context),
        *history,
    ]

    def _invoke(msgs: list[BaseMessage]) -> list[BaseMessage]:
        try:
            result = agent.invoke(
                {"messages": msgs},
                config={"recursion_limit": RECURSION_LIMIT},
            )
        except Exception as exc:  # noqa: BLE001 - classified and re-raised below
            logger.exception(
                "Assistant run failed (cart_id=%s, user_id=%s)", cart_id, user_id
            )
            raise AssistantError(_classify(exc), cause=exc) from exc
        return result.get("messages", [])

    def _last_reply(msgs: list[BaseMessage]) -> str:
        for message in reversed(msgs):
            if isinstance(message, AIMessage):
                text = _message_text(message)
                if text:
                    return text
        return ""

    result_messages = _invoke(messages)
    reply = _last_reply(result_messages)

    # The model sometimes describes adding items without calling the tool.
    # Tell it so once; if it still has not acted, do not pass the claim on.
    if (
        reply
        and not mutation_log.cart_changed
        and _CLAIMS_CHANGE_RE.search(reply)
    ):
        logger.warning(
            "Assistant claimed a cart change it did not make (cart_id=%s); "
            "retrying once",
            cart_id,
        )
        result_messages = _invoke(
            [*result_messages, HumanMessage(content=UNDONE_CHANGE_NUDGE)]
        )
        reply = _last_reply(result_messages)
        if not mutation_log.cart_changed and _CLAIMS_CHANGE_RE.search(reply):
            reply = _UNDONE_CHANGE_FALLBACK

    if not reply:
        # The model finished on a tool call without summarising. Say something
        # truthful rather than returning an empty bubble.
        if mutation_log.cart_changed:
            reply = "I have updated the cart."
        else:
            reply = "I could not find anything to add for that. Could you rephrase?"

    return reply, mutation_log


__all__ = ["AssistantError", "run_shopping_assistant"]
