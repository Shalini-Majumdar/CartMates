from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas.schemas import AskRequest, MessageCreate, ParsedResponse, CartItemResponse, ResMessage
from models.models import Message
from crud.crud import create_message, add_items_to_cart

import re
from typing import Optional, List
import json
from agent.llm_agent import recommend_products

router = APIRouter(prefix="/messages", tags=["messages"])

def dummy(list_of_msgs) -> str:
    print("=== Debug messages ===")
    for msg in list_of_msgs:
        print(f"[{msg['sender_type']}] {msg['message_content']}")
    print("======================")
    return "assistant_response"

def extract_json_from_code_block(text: str) -> Optional[str]:
    """Extract JSON from code block in LLM response"""
    pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    return None

def remove_code_block(text: str) -> str:
    """Remove code block from text, leaving only the message"""
    return re.sub(r"```(?:json)?\s*\{.*?\}\s*```", "", text, flags=re.DOTALL).strip()

def parse_llm_response(content: str) -> ParsedResponse:
    """Parse LLM response to extract message and items to add to cart"""
    try:
        json_str = extract_json_from_code_block(content)
        if json_str:
            response_json = json.loads(json_str)
            items_raw = response_json.get("items", [])
            
            items = []
            for entry in items_raw:
                items.append(
                    CartItemResponse(
                        product_id=entry.get("product_id"),
                        quantity=entry.get("quantity", 1)
                    )
                )
        else:
            items = []
        
        # Extract message by removing code block
        message_text = remove_code_block(content).strip()
        
        return ParsedResponse(
            message=message_text,
            items=items,
            error=None
        )
    except Exception as e:
        return ParsedResponse(
            message=content,  # Return original content if parsing fails
            items=[],
            error=f"Error parsing response: {str(e)}"
        )

@router.post("/ask")
def ask_assistant(request: AskRequest, db: Session = Depends(get_db)):
    """
    Accepts cart_id and user message.
    Stores user message, fetches all messages, gets assistant reply, 
    parses the response, adds items to cart, and returns the message.
    """
    try:
        # Save the user's message first
        user_msg = MessageCreate(
            cart_id=request.cart_id,
            sender_id=request.user_id,
            sender_type="user",
            message_content=request.message
        )
        create_message(db, user_msg)

        # Fetch all messages from DB
        messages_in_db = (
            db.query(Message)
            .filter(Message.cart_id == request.cart_id)
            .order_by(Message.timestamp.asc())
            .all()
        )

        # Convert them to string format for the agent
        compiled_messages = "\n".join(
            f"[{msg.sender_type}] {msg.message_content}" for msg in messages_in_db
        )

        # Call the agent to get recommendation
        agent_response = recommend_products(compiled_messages, request.cart_id)

        # Parse the agent response
        parsed_response = parse_llm_response(agent_response)

        # Add items to cart if any were recommended
        cart_updates = []
        if parsed_response.items:
            cart_updates = add_items_to_cart(
                db, request.cart_id, request.user_id, parsed_response.items
            )

        # Prepare the final message
        final_message = parsed_response.message
        if cart_updates:
            final_message += f"\n\nCart Updates:\n" + "\n".join(f"• {update}" for update in cart_updates)

        # Save assistant reply (without the JSON part)
        ASSISTANT_USER_ID = 1  # Use your real assistant user ID
        assistant_msg = MessageCreate(
            cart_id=request.cart_id,
            sender_id=ASSISTANT_USER_ID,
            sender_type="assistant",
            message_content=final_message
        )
        create_message(db, assistant_msg)

        return {
            "cart_id": request.cart_id,
            "user_message": request.message,
            "assistant_response": final_message,
            "items_added": len(parsed_response.items),
            "error": parsed_response.error
        }

    except Exception as e:
        # Handle any unexpected errors
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        
        # Still save an error message from assistant
        try:
            ASSISTANT_USER_ID = 1
            error_assistant_msg = MessageCreate(
                cart_id=request.cart_id,
                sender_id=ASSISTANT_USER_ID,
                sender_type="assistant",
                message_content=error_msg
            )
            create_message(db, error_assistant_msg)
        except:
            pass  # If we can't save the error message, don't crash further
        
        return {
            "cart_id": request.cart_id,
            "user_message": request.message,
            "assistant_response": error_msg,
            "items_added": 0,
            "error": str(e)
        }


from sqlalchemy.orm import joinedload
from fastapi import HTTPException

@router.get("/{cart_id}", response_model=List[ResMessage])
def get_messages(cart_id: int, db: Session = Depends(get_db)):
    """
    Fetch all messages for a given cart, including sender username.
    """
    # Fetch messages and eager-load the sender relationship
    messages = (
        db.query(Message)
        .options(joinedload(Message.sender))
        .filter(Message.cart_id == cart_id)
        .order_by(Message.timestamp.asc())
        .all()
    )

    if not messages:
        raise HTTPException(status_code=404, detail="No messages found for this cart.")

    result = []
    for msg in messages:
        result.append(
            ResMessage(
                message_id=msg.message_id,
                cart_id=msg.cart_id,
                sender_id=msg.sender_id,
                sender_type=msg.sender_type,
                sender_name=msg.sender.user_name if msg.sender else None,
                message_content=msg.message_content,
                timestamp=msg.timestamp,
            )
        )

    return result
