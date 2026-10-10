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

# Tried in order. Each model has its own free-tier quota, so when one is used
# up (or retired) the next one answers instead. The lite models come first:
# their suggestions are a little weaker but their free allowance goes further.
# Override with a comma-separated GEMINI_MODELS in .env.
DEFAULT_MODELS = "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-2.5-flash"
MODEL_NAMES = [
    name.strip()
    for name in os.getenv("GEMINI_MODELS", DEFAULT_MODELS).split(",")
    if name.strip()
]
# Low temperature suits tool selection and budget arithmetic on Gemini 2.x.
# Google recommends leaving Gemini 3 at its default of 1.0; lower values can
# make it loop.
LEGACY_TEMPERATURE = 0.1
GEMINI_3_TEMPERATURE = 1.0
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

_PARTIAL_CHANGE_REPLY = (
    "I made some changes to the cart but could not finish. Please check the "
    "items and ask again for anything still missing."
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


def _build_llms() -> list[ChatGoogleGenerativeAI]:
    if not os.getenv("GOOGLE_API_KEY"):
        logger.warning("GOOGLE_API_KEY is not set; the assistant is disabled.")
        return []
    return [
        ChatGoogleGenerativeAI(
            model=name,
            temperature=(
                GEMINI_3_TEMPERATURE if name.startswith("gemini-3") else LEGACY_TEMPERATURE
            ),
            timeout=REQUEST_TIMEOUT_SECONDS,
            # One quick retry for a blip; a spent quota falls through to the
            # next model instead of waiting here.
            max_retries=1,
        )
        for name in MODEL_NAMES
    ]


# Model clients are stateless and safe to share; the agent graph is rebuilt
# per request because its tools are bound to that request's cart and user.
_llms = _build_llms()


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


def _should_try_next_model(exc: BaseException) -> bool:
    """Failures another model may not share: a spent quota, a retired model,
    or an overloaded one."""
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    return (
        "resourceexhausted" in name
        or "resource_exhausted" in text
        or "quota" in text
        or "429" in text
        or "notfound" in name
        or "not_found" in text
        or "no longer available" in text
        or "503" in text
        or "overloaded" in text
        or "unavailable" in text
    )


def _classify(exc: BaseException) -> str:
    """Map a failure to a message worth showing the user."""
    name = type(exc).__name__
    text = str(exc).lower()

    if name == "GraphRecursionError":
        return (
            "That turned out to be more involved than I could work through in "
            "one go. Could you narrow it down a little?"
        )
    if (
        "resourceexhausted" in name.lower()
        or "resource_exhausted" in text
        or "quota" in text
        or "rate limit" in text
    ):
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
    if not _llms:
        raise AssistantError(
            "The shopping assistant is not configured yet, so I cannot help "
            "with the cart right now."
        )
    if not history:
        raise AssistantError("There was no message for me to reply to.")

    tools, mutation_log = build_tools(db=db, cart_id=cart_id, user_id=user_id)

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

    agents = [(llm.model, create_react_agent(llm, tools)) for llm in _llms]

    def _invoke(msgs: list[BaseMessage]) -> list[BaseMessage]:
        last_exc: Optional[BaseException] = None
        for model_name, agent in agents:
            try:
                result = agent.invoke(
                    {"messages": msgs},
                    config={"recursion_limit": RECURSION_LIMIT},
                )
                return result.get("messages", [])
            except Exception as exc:  # noqa: BLE001 - classified below
                last_exc = exc
                # Once the cart has changed, starting over on another model
                # could add the same items twice, so stop here instead.
                if _should_try_next_model(exc) and not mutation_log.cart_changed:
                    logger.warning(
                        "Model %s unavailable (%s); trying the next one",
                        model_name,
                        str(exc).splitlines()[0][:200],
                    )
                    continue
                break

        if mutation_log.cart_changed:
            # Part of the work was done before the failure. Report it rather
            # than an error that suggests nothing happened.
            logger.warning(
                "Assistant stopped after changing the cart (cart_id=%s): %s",
                cart_id,
                last_exc,
            )
            return [AIMessage(content=_PARTIAL_CHANGE_REPLY)]

        logger.error(
            "Assistant run failed on every model (cart_id=%s, user_id=%s)",
            cart_id,
            user_id,
            exc_info=last_exc,
        )
        raise AssistantError(_classify(last_exc), cause=last_exc) from last_exc

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
