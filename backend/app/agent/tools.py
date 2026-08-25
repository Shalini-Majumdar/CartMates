# agent/tools.py

import re
from langchain.agents import Tool
import psycopg2
from agent.connection import get_connection
import json

# Helper to parse LLM string input like 'query: stationary, budget: 50.0'
def parse_query_budget(input_str):
    match = re.match(r"query: ?(.+), ?budget: ?([0-9.]+)", input_str, re.IGNORECASE)
    if match:
        query = match.group(1).strip().strip('"\'')
        budget = float(match.group(2))
        # Fallback: if query is 'groceries', 'grocery', or 'food', search the Groceries category
        if query.lower() in ['groceries', 'grocery', 'food']:
            query = 'Groceries'
        return query, budget
    return input_str, None

def get_all_categories() -> str:
    print("[DEBUG] get_all_categories called")
    conn = None
    try:
        conn = get_connection()
        print(f"[DEBUG] Connected to DB: {getattr(conn, 'dsn', 'no dsn')}")
        cursor = conn.cursor()
        print(f"[DEBUG] Cursor type: {type(cursor)}")
        sql = "SELECT DISTINCT category FROM products WHERE category IS NOT NULL;"
        print(f"[DEBUG] Executing SQL: {sql}")
        cursor.execute(sql)
        rows = cursor.fetchall()
        print(f"[DEBUG] Raw fetchall() result: {rows}")
        if not rows:
            print("[ERROR] No categories found in products table!")
            return ""
        # Try both tuple and dict access
        try:
            categories = [row[0] for row in rows if row[0]]
        except Exception as e:
            print(f"[DEBUG] Tuple access failed: {e}, trying dict access")
            categories = [row['category'] for row in rows if row['category']]
        result = ", ".join(categories)
        print(f"[DEBUG] get_all_categories result: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] Failed to fetch categories: {e} (type: {type(e)})")
        return ""
    finally:
        if conn:
            conn.close()

def search_products(query: str, budget: float) -> list[dict]:
    print(f"[DEBUG] search_products called with query='{query}', budget={budget}")
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = (
            """
            SELECT
                product_id,          
                product_name,     
                product_description, 
                image_url,       
                price
            FROM products
            WHERE (LOWER(category) LIKE %s OR LOWER(product_description) LIKE %s)
              AND price <= %s
            ORDER BY price ASC
            LIMIT 10;
            """
        )
        query_param = f"%{query.lower()}%"
        params = (query_param, query_param, budget)
        print(f"[DEBUG] Executing SQL: {sql.strip()} with params {params}")
        cursor.execute(sql, params)
        results = cursor.fetchall()
        print(f"[DEBUG] search_products results: {results}")
        return results
    except psycopg2.Error as e:
        print(f"[ERROR] Database error in search_products: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in search_products: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_cart_contents(cart_id: int) -> list[int]:
    print(f"[DEBUG] get_cart_contents called with cart_id={cart_id}")
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = "SELECT product_id FROM cart_items WHERE cart_id = %s;"
        print(f"[DEBUG] Executing SQL: {sql.strip()} with cart_id={cart_id}")
        cursor.execute(sql, (cart_id,))
        product_ids = [row["product_id"] for row in cursor.fetchall()]
        print(f"[DEBUG] get_cart_contents results: {product_ids}")
        return product_ids
    except psycopg2.Error as e:
        print(f"[ERROR] Database error in get_cart_contents: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in get_cart_contents: {e}")
        return []
    finally:
        if conn:
            conn.close()

# Wrapper functions that handle input parsing clearly
def clean_json_input(input_str: str) -> str:
    """Remove markdown code blocks and clean JSON input"""
    # Remove ```json and ``` markers
    cleaned = input_str.strip()
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]  # Remove ```json
    if cleaned.startswith('```'):
        cleaned = cleaned[3:]   # Remove ```
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]  # Remove trailing ```
    return cleaned.strip()

def search_products_wrapper(input_str: str):
    """Parse input and call search_products"""
    try:
        cleaned_input = clean_json_input(input_str)
        print(f"[DEBUG] search_products_wrapper received: '{input_str}'")
        print(f"[DEBUG] cleaned input: '{cleaned_input}'")
        
        # Try to parse as JSON first
        if cleaned_input.startswith('{'):
            data = json.loads(cleaned_input)
            return search_products(data['query'], data['budget'])
        else:
            # Parse as "query: X, budget: Y" format
            query, budget = parse_query_budget(cleaned_input)
            if budget is None:
                return f"Error: Invalid input format. Expected JSON like {{'query': 'search_term', 'budget': 45.0}}"
            return search_products(query, budget)
    except Exception as e:
        return f"Error parsing input: {e}. Input received: '{input_str}'"

def get_cart_contents_wrapper(input_str: str):
    """Parse input and call get_cart_contents"""
    try:
        cleaned_input = clean_json_input(input_str)
        print(f"[DEBUG] get_cart_contents_wrapper received: '{input_str}'")
        print(f"[DEBUG] cleaned input: '{cleaned_input}'")
        
        # Try to parse as JSON first
        if cleaned_input.startswith('{'):
            data = json.loads(cleaned_input)
            return get_cart_contents(data['cart_id'])
        else:
            # Parse as plain number
            cart_id = int(cleaned_input.strip())
            return get_cart_contents(cart_id)
    except Exception as e:
        return f"Error parsing input: {e}. Input received: '{input_str}'"

tools = [
    Tool(
        name="search_products",
        func=search_products_wrapper,
        description=(
            "Search for products within a specific budget. "
            "INPUT: JSON object with 'query' and 'budget' fields. "
            "Example: {\"query\": \"beach products\", \"budget\": 45.0} "
            "- query: search term or product category (string) "
            "- budget: maximum price per item (number) "
            "Returns: List of products with product_id, product_name, product_description, image_url, and price. "
            "Use this to find products matching user requirements."
        )
    ),
    Tool(
        name="get_cart_contents",
        func=get_cart_contents_wrapper,
        description=(
            "Get all product IDs currently in a shopping cart. "
            "INPUT: JSON object with 'cart_id' field. "
            "Example: {\"cart_id\": 1} "
            "- cart_id: the cart identifier (number) "
            "Returns: List of product IDs (integers) currently in the cart. "
            "Use this to check what's already in the cart before adding new items."
        )
    ),
]