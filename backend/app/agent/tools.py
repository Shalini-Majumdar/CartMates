# agent/tools.py
"""Tools the shopping assistant can call.

Every tool is bound at request time to one cart and one user. The model never
sees a cart_id and has no way to supply one, so it cannot read or modify a cart
the caller does not belong to.

Tools return short, plain-text strings written for the model: compact rows, no
image URLs, truncated descriptions, and a usable sentence when there is nothing
to report so the agent can recover instead of seeing an empty list.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from models.models import CartItem, Product

logger = logging.getLogger(__name__)

MAX_SEARCH_RESULTS = 10
MAX_DESCRIPTION_CHARS = 100
MAX_ITEMS_PER_CALL = 20
# Query words shorter than this ("a", "of", "for") match almost everything.
MIN_SEARCH_WORD_LENGTH = 3


# --------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------


def _money(value) -> str:
    return f"${Decimal(str(value)):.2f}"


def _truncate(text: Optional[str], limit: int = MAX_DESCRIPTION_CHARS) -> str:
    if not text:
        return "no description"
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _format_product(product: Product) -> str:
    return (
        f"product_id={product.product_id} | {product.product_name} | "
        f"{_money(product.price)} | {product.category or 'Uncategorised'} | "
        f"{_truncate(product.product_description)}"
    )


# --------------------------------------------------------------------------
# Argument schemas — these become the function-calling schema sent to Gemini,
# so the descriptions are load-bearing.
# --------------------------------------------------------------------------


class SearchProductsArgs(BaseModel):
    query: str = Field(
        description=(
            "Category name or keyword to search for, e.g. 'Groceries' or "
            "'toothpaste'. Matches product names, descriptions and categories."
        )
    )
    max_price: Optional[float] = Field(
        default=None,
        description=(
            "Maximum price per item, in dollars. Omit entirely when the user "
            "gave no budget — do not invent one."
        ),
    )


class ProductDetailsArgs(BaseModel):
    product_id: int = Field(description="The product_id to look up.")


class ItemToAdd(BaseModel):
    product_id: int = Field(
        description="A product_id returned by search_products or get_product_details."
    )
    quantity: int = Field(
        default=1, ge=1, description="How many units to add. Must be at least 1."
    )


class AddItemsArgs(BaseModel):
    items: list[ItemToAdd] = Field(
        description="The items to add. Add everything in one call rather than one per item."
    )


class UpdateQuantityArgs(BaseModel):
    product_id: int = Field(description="The product_id of an item already in the cart.")
    quantity: int = Field(
        ge=1,
        description="The new total quantity. To remove the item entirely use remove_item.",
    )


class RemoveItemArgs(BaseModel):
    product_id: int = Field(description="The product_id of the item to remove.")


# --------------------------------------------------------------------------
# Mutation log — lets the caller know whether the cart actually changed
# without re-parsing the assistant's prose.
# --------------------------------------------------------------------------


@dataclass
class CartMutationLog:
    items_added: int = 0
    items_updated: int = 0
    items_removed: int = 0
    details: list[str] = field(default_factory=list)

    @property
    def cart_changed(self) -> bool:
        return bool(self.items_added or self.items_updated or self.items_removed)


# --------------------------------------------------------------------------
# Tool factory
# --------------------------------------------------------------------------


def build_tools(db: Session, cart_id: int, user_id: int):
    """Build the tool set for one request.

    Returns (tools, mutation_log). cart_id and user_id are captured here and
    are never exposed to the model.
    """

    log = CartMutationLog()

    def _cart_item_for(product_id: int) -> Optional[CartItem]:
        """Find a product's row in this cart, preferring the current user's."""
        rows = (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
            .all()
        )
        if not rows:
            return None
        for row in rows:
            if row.added_by == user_id:
                return row
        return rows[0]

    # -- read-only tools --------------------------------------------------

    def get_categories() -> str:
        """List every product category the store stocks."""
        try:
            rows = (
                db.query(Product.category)
                .filter(Product.category.isnot(None))
                .distinct()
                .order_by(Product.category)
                .all()
            )
        except Exception:
            logger.exception("get_categories failed")
            return "The product catalogue is unavailable right now."

        categories = [row[0] for row in rows if row[0]]
        if not categories:
            return "The catalogue has no categories yet."
        return "Available categories: " + ", ".join(categories)

    def _search_terms(query: str) -> list[str]:
        """The whole phrase plus each word, with a plural 's' dropped.

        Matching any word means "salty snacks" still finds "Potato Chips" in
        the Snacks category, and "drinks" finds a "drink" in a description.
        """
        phrase = query.lower().strip()
        terms = [phrase] if phrase else []
        for word in re.findall(r"[a-z0-9]+", phrase):
            if len(word) < MIN_SEARCH_WORD_LENGTH:
                continue
            if word.endswith("s") and len(word) > MIN_SEARCH_WORD_LENGTH:
                word = word[:-1]
            if word not in terms:
                terms.append(word)
        return terms

    def search_products(query: str, max_price: Optional[float] = None) -> str:
        """Search the catalogue by keyword or category, optionally under a price."""
        try:
            conditions = []
            for term in _search_terms(query):
                pattern = f"%{term}%"
                conditions += [
                    func.lower(Product.category).like(pattern),
                    func.lower(Product.product_name).like(pattern),
                    func.lower(Product.product_description).like(pattern),
                ]
            if not conditions:
                return "Give a keyword or category to search for."
            base = db.query(Product).filter(or_(*conditions))

            filtered = base
            if max_price is not None:
                filtered = filtered.filter(Product.price <= Decimal(str(max_price)))

            products = (
                filtered.order_by(Product.price.asc()).limit(MAX_SEARCH_RESULTS).all()
            )

            if products:
                header = f"{len(products)} match(es) for '{query}'"
                if max_price is not None:
                    header += f" at or below {_money(max_price)}"
                lines = [_format_product(p) for p in products]
                return header + ":\n" + "\n".join(lines)

            # Nothing matched: say something the agent can act on.
            if max_price is not None:
                cheapest = base.order_by(Product.price.asc()).first()
                if cheapest is not None:
                    return (
                        f"No products matching '{query}' at or below "
                        f"{_money(max_price)}. The cheapest match is "
                        f"{_format_product(cheapest)}."
                    )
            # Hand back the categories in the same result, so the agent can
            # retry straight away instead of ending its turn on a dead end.
            return (
                f"No products match '{query}'. {get_categories()} "
                f"Search again now using the closest of these categories."
            )
        except Exception:
            logger.exception("search_products failed (query=%r)", query)
            return "The product catalogue is unavailable right now."

    def get_product_details(product_id: int) -> str:
        """Look up one product by id, to confirm it exists before adding it."""
        try:
            product = (
                db.query(Product).filter(Product.product_id == product_id).first()
            )
        except Exception:
            logger.exception("get_product_details failed (product_id=%s)", product_id)
            return "The product catalogue is unavailable right now."

        if product is None:
            return (
                f"There is no product with product_id={product_id}. "
                f"Use search_products to find a real one."
            )
        return _format_product(product)

    def get_cart_summary() -> str:
        """Show what is already in this cart, with quantities and totals."""
        try:
            items = (
                db.query(CartItem)
                .options(joinedload(CartItem.product))
                .filter(CartItem.cart_id == cart_id)
                .all()
            )
        except Exception:
            logger.exception("get_cart_summary failed (cart_id=%s)", cart_id)
            return "The cart is unavailable right now."

        if not items:
            return "The cart is empty."

        lines = []
        total = Decimal("0.00")
        approved_total = Decimal("0.00")
        for item in items:
            product = item.product
            if product is None:
                continue
            unit = Decimal(str(product.price))
            line_total = unit * item.quantity
            total += line_total
            if item.approved:
                approved_total += line_total
            lines.append(
                f"product_id={product.product_id} | {product.product_name} | "
                f"qty {item.quantity} | {_money(unit)} each | {_money(line_total)} | "
                f"{'approved' if item.approved else 'pending approval'}"
            )

        summary = (
            f"Cart total: {_money(total)} across {len(lines)} item(s) "
            f"({_money(approved_total)} approved)."
        )
        return "\n".join(lines) + "\n" + summary

    # -- write tools ------------------------------------------------------

    def add_items_to_cart(items: list[ItemToAdd]) -> str:
        """Add products to this cart. Items start unapproved for the members to review."""
        if not items:
            return "No items were given, so nothing was added."
        if len(items) > MAX_ITEMS_PER_CALL:
            return (
                f"Too many items in one call ({len(items)}); "
                f"add at most {MAX_ITEMS_PER_CALL} at a time."
            )

        results = []
        try:
            for entry in items:
                product = (
                    db.query(Product)
                    .filter(Product.product_id == entry.product_id)
                    .first()
                )
                if product is None:
                    results.append(
                        f"No product with product_id={entry.product_id}; skipped."
                    )
                    continue

                existing = _cart_item_for(entry.product_id)
                if existing is not None:
                    existing.quantity += entry.quantity
                    log.items_updated += 1
                    message = (
                        f"{product.product_name} was already in the cart; "
                        f"quantity is now {existing.quantity}."
                    )
                else:
                    db.add(
                        CartItem(
                            cart_id=cart_id,
                            product_id=entry.product_id,
                            added_by=user_id,
                            quantity=entry.quantity,
                            approved=False,
                        )
                    )
                    log.items_added += 1
                    message = (
                        f"Added {entry.quantity}× {product.product_name} "
                        f"({_money(product.price)} each)."
                    )
                results.append(message)
                log.details.append(message)

            db.commit()
        except Exception:
            db.rollback()
            logger.exception("add_items_to_cart failed (cart_id=%s)", cart_id)
            return "Could not update the cart because of a database error."

        return "\n".join(results)

    def update_quantity(product_id: int, quantity: int) -> str:
        """Set the quantity of an item already in this cart."""
        try:
            item = _cart_item_for(product_id)
            if item is None:
                return (
                    f"product_id={product_id} is not in the cart. "
                    f"Call get_cart_summary to see what is."
                )
            name = item.product.product_name if item.product else f"product {product_id}"
            item.quantity = quantity
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("update_quantity failed (product_id=%s)", product_id)
            return "Could not update the cart because of a database error."

        log.items_updated += 1
        message = f"Set {name} to quantity {quantity}."
        log.details.append(message)
        return message

    def remove_item(product_id: int) -> str:
        """Remove an item from this cart entirely."""
        try:
            item = _cart_item_for(product_id)
            if item is None:
                return (
                    f"product_id={product_id} is not in the cart, so there is "
                    f"nothing to remove."
                )
            name = item.product.product_name if item.product else f"product {product_id}"
            db.delete(item)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("remove_item failed (product_id=%s)", product_id)
            return "Could not update the cart because of a database error."

        log.items_removed += 1
        message = f"Removed {name} from the cart."
        log.details.append(message)
        return message

    tools = [
        StructuredTool.from_function(
            func=get_categories,
            name="get_categories",
            description=(
                "List every product category the store stocks. Call this before "
                "searching so you only search categories that exist."
            ),
        ),
        StructuredTool.from_function(
            func=search_products,
            name="search_products",
            description=(
                "Search the catalogue by keyword or category, cheapest first. "
                "Returns up to 10 rows of product_id, name, price and category. "
                "Always search before adding anything: never invent a product_id."
            ),
            args_schema=SearchProductsArgs,
        ),
        StructuredTool.from_function(
            func=get_product_details,
            name="get_product_details",
            description="Look up one product by product_id to confirm it exists.",
            args_schema=ProductDetailsArgs,
        ),
        StructuredTool.from_function(
            func=get_cart_summary,
            name="get_cart_summary",
            description=(
                "Show what is already in the cart: each item's product_id, name, "
                "quantity, unit price and line total, plus the cart total. Call "
                "this before recommending anything so you neither duplicate items "
                "nor blow the budget."
            ),
        ),
        StructuredTool.from_function(
            func=add_items_to_cart,
            name="add_items_to_cart",
            description=(
                "Add one or more products to the cart. Pass every item in a "
                "single call. Items are added unapproved for the cart members "
                "to review. Returns what was actually added."
            ),
            args_schema=AddItemsArgs,
        ),
        StructuredTool.from_function(
            func=update_quantity,
            name="update_quantity",
            description=(
                "Set the quantity of an item already in the cart, e.g. when the "
                "user says 'make it 3'."
            ),
            args_schema=UpdateQuantityArgs,
        ),
        StructuredTool.from_function(
            func=remove_item,
            name="remove_item",
            description="Remove an item from the cart entirely.",
            args_schema=RemoveItemArgs,
        ),
    ]

    return tools, log
