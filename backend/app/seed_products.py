"""Load a starter product catalogue into an empty database.

Run from the package directory (as docker-compose does):

    python seed_products.py

It only inserts when the products table is empty, so it is safe to run on
every start and never duplicates products. It also swaps the grey placeholder
images from earlier seeds for the real photos in frontend/public/products,
leaving any image you have set yourself alone.
"""

import re
from decimal import Decimal

from database import SessionLocal
from models.models import Product

# (name, description, price in rupees, category)
CATALOGUE = [
    # Snacks
    ("Salted Potato Chips", "Classic crispy potato chips, 150 g family pack.", "219", "Snacks"),
    ("Nacho Tortilla Chips", "Corn tortilla chips, great with salsa or dip, 200 g.", "263", "Snacks"),
    ("Butter Popcorn", "Microwave popcorn, pack of 3 bags.", "307", "Snacks"),
    ("Roasted Salted Peanuts", "Dry roasted peanuts, 300 g jar.", "351", "Snacks"),
    ("Trail Mix", "Nuts, raisins and chocolate chips, 400 g resealable bag.", "527", "Snacks"),
    ("Chocolate Chip Cookies", "Soft baked cookies, pack of 12.", "290", "Snacks"),
    ("Granola Bars", "Oats and honey bars, box of 10.", "395", "Snacks"),
    ("Milk Chocolate Bar", "Smooth milk chocolate, 100 g.", "175", "Snacks"),
    ("Tomato Salsa Dip", "Medium spicy salsa, 300 g jar.", "246", "Snacks"),
    # Beverages
    ("Sparkling Water 6-Pack", "Unflavoured sparkling mineral water, 6 x 500 ml.", "351", "Beverages"),
    ("Orange Juice", "100% orange juice, no added sugar, 1 L.", "307", "Beverages"),
    ("Cola 12-Pack", "Classic cola, 12 x 330 ml cans.", "615", "Beverages"),
    ("Green Tea Bags", "Pure green tea, box of 50 bags.", "378", "Beverages"),
    ("Ground Coffee", "Medium roast ground coffee, 250 g.", "571", "Beverages"),
    ("Bottled Water 24-Pack", "Still drinking water, 24 x 500 ml.", "483", "Beverages"),
    # Breakfast
    ("Whole Wheat Bread", "Sliced whole wheat loaf, 400 g.", "202", "Breakfast"),
    ("Free Range Eggs", "Dozen large free range eggs.", "369", "Breakfast"),
    ("Rolled Oats", "Whole grain rolled oats, 1 kg.", "281", "Breakfast"),
    ("Corn Flakes", "Crispy corn flakes cereal, 500 g.", "316", "Breakfast"),
    ("Strawberry Jam", "Strawberry fruit spread, 350 g jar.", "254", "Breakfast"),
    ("Peanut Butter", "Creamy peanut butter, 450 g jar.", "334", "Breakfast"),
    # Dairy
    ("Whole Milk", "Fresh whole milk, 1 L.", "131", "Dairy"),
    ("Greek Yogurt", "Plain Greek yogurt, 500 g tub.", "290", "Dairy"),
    ("Cheddar Cheese Block", "Mature cheddar, 200 g.", "351", "Dairy"),
    ("Salted Butter", "Salted butter, 250 g block.", "263", "Dairy"),
    # Fruits & Vegetables
    ("Bananas", "Bunch of 6 ripe bananas.", "166", "Fruits & Vegetables"),
    ("Red Apples", "Crisp red apples, 1 kg bag.", "307", "Fruits & Vegetables"),
    ("Baby Carrots", "Washed baby carrots, 500 g.", "175", "Fruits & Vegetables"),
    ("Cherry Tomatoes", "Sweet cherry tomatoes, 250 g punnet.", "219", "Fruits & Vegetables"),
    ("Mixed Salad Leaves", "Ready-to-eat salad mix, 200 g.", "202", "Fruits & Vegetables"),
    # Pantry
    ("Spaghetti", "Durum wheat spaghetti, 500 g.", "140", "Pantry"),
    ("Pasta Sauce", "Tomato and basil pasta sauce, 500 g jar.", "263", "Pantry"),
    ("Basmati Rice", "Long grain basmati rice, 1 kg.", "342", "Pantry"),
    ("Instant Noodles 5-Pack", "Chicken flavour instant noodles, 5 packs.", "219", "Pantry"),
    ("Baked Beans", "Baked beans in tomato sauce, 400 g can.", "114", "Pantry"),
    # Toiletries
    ("Toothpaste", "Fluoride toothpaste, mint, 100 ml.", "219", "Toiletries"),
    ("Toothbrush 2-Pack", "Medium bristle toothbrushes, pack of 2.", "290", "Toiletries"),
    ("Shampoo", "Daily care shampoo for all hair types, 400 ml.", "439", "Toiletries"),
    ("Body Wash", "Moisturising body wash, 500 ml.", "395", "Toiletries"),
    ("Deodorant", "48-hour roll-on deodorant, 50 ml.", "307", "Toiletries"),
    ("Hand Soap", "Liquid hand soap with pump, 250 ml.", "175", "Toiletries"),
    # Household
    ("Toilet Paper 12-Roll", "Soft 3-ply toilet paper, 12 rolls.", "703", "Household"),
    ("Paper Towels 4-Roll", "Absorbent kitchen paper towels, 4 rolls.", "439", "Household"),
    ("Dish Soap", "Lemon dishwashing liquid, 750 ml.", "246", "Household"),
    ("Trash Bags", "Heavy duty 30 L trash bags, 40 count.", "483", "Household"),
    ("Disposable Plates", "Sturdy paper plates, pack of 50.", "378", "Household"),
    ("Disposable Cups", "Paper cups, 250 ml, pack of 50.", "334", "Household"),
    # Outdoor & Travel
    ("Sunscreen SPF 50", "Water resistant sunscreen lotion, 200 ml.", "791", "Outdoor & Travel"),
    ("Insect Repellent", "DEET-free insect repellent spray, 100 ml.", "571", "Outdoor & Travel"),
    ("LED Flashlight", "Compact LED flashlight with batteries.", "879", "Outdoor & Travel"),
    ("AA Batteries 8-Pack", "Long-lasting alkaline AA batteries.", "659", "Outdoor & Travel"),
    ("First Aid Kit", "Travel first aid kit, 40 pieces.", "1143", "Outdoor & Travel"),
    ("Wet Wipes", "Fragrance-free wet wipes, 80 count.", "263", "Outdoor & Travel"),
]


# Earlier seeds priced the same products in US dollars. A product still at its
# old dollar price is converted once at USD_TO_INR; edited prices are kept.
USD_TO_INR = Decimal("88")
LEGACY_USD_PRICES = {
    "Salted Potato Chips": "2.49",
    "Nacho Tortilla Chips": "2.99",
    "Butter Popcorn": "3.49",
    "Roasted Salted Peanuts": "3.99",
    "Trail Mix": "5.99",
    "Chocolate Chip Cookies": "3.29",
    "Granola Bars": "4.49",
    "Milk Chocolate Bar": "1.99",
    "Tomato Salsa Dip": "2.79",
    "Sparkling Water 6-Pack": "3.99",
    "Orange Juice": "3.49",
    "Cola 12-Pack": "6.99",
    "Green Tea Bags": "4.29",
    "Ground Coffee": "6.49",
    "Bottled Water 24-Pack": "5.49",
    "Whole Wheat Bread": "2.29",
    "Free Range Eggs": "4.19",
    "Rolled Oats": "3.19",
    "Corn Flakes": "3.59",
    "Strawberry Jam": "2.89",
    "Peanut Butter": "3.79",
    "Whole Milk": "1.49",
    "Greek Yogurt": "3.29",
    "Cheddar Cheese Block": "3.99",
    "Salted Butter": "2.99",
    "Bananas": "1.89",
    "Red Apples": "3.49",
    "Baby Carrots": "1.99",
    "Cherry Tomatoes": "2.49",
    "Mixed Salad Leaves": "2.29",
    "Spaghetti": "1.59",
    "Pasta Sauce": "2.99",
    "Basmati Rice": "3.89",
    "Instant Noodles 5-Pack": "2.49",
    "Baked Beans": "1.29",
    "Toothpaste": "2.49",
    "Toothbrush 2-Pack": "3.29",
    "Shampoo": "4.99",
    "Body Wash": "4.49",
    "Deodorant": "3.49",
    "Hand Soap": "1.99",
    "Toilet Paper 12-Roll": "7.99",
    "Paper Towels 4-Roll": "4.99",
    "Dish Soap": "2.79",
    "Trash Bags": "5.49",
    "Disposable Plates": "4.29",
    "Disposable Cups": "3.79",
    "Sunscreen SPF 50": "8.99",
    "Insect Repellent": "6.49",
    "LED Flashlight": "9.99",
    "AA Batteries 8-Pack": "7.49",
    "First Aid Kit": "12.99",
    "Wet Wipes": "2.99",
}

PLACEHOLDER_PREFIX = "https://placehold.co/"


def _image_for(name: str) -> str:
    """Served by the frontend from frontend/public/products (see CREDITS.md)."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"/products/{slug}.jpg"


def _replace_placeholder_images(db) -> int:
    names = {name for name, *_ in CATALOGUE}
    updated = 0
    for product in (
        db.query(Product)
        .filter(Product.image_url.like(f"{PLACEHOLDER_PREFIX}%"))
        .all()
    ):
        if product.product_name in names:
            product.image_url = _image_for(product.product_name)
            updated += 1
    db.commit()
    return updated


def _convert_legacy_dollar_prices(db) -> int:
    inr_prices = {name: Decimal(price) for name, _, price, _ in CATALOGUE}
    converted = 0
    for product in db.query(Product).filter(
        Product.product_name.in_(list(LEGACY_USD_PRICES))
    ):
        if product.price == Decimal(LEGACY_USD_PRICES[product.product_name]):
            product.price = inr_prices[product.product_name]
            converted += 1
    db.commit()
    return converted


def main() -> None:
    db = SessionLocal()
    try:
        if db.query(Product).first() is not None:
            updated = _replace_placeholder_images(db)
            converted = _convert_legacy_dollar_prices(db)
            print(
                "seed_products: products already present; "
                f"replaced {updated} placeholder image(s), "
                f"converted {converted} price(s) from USD to INR."
            )
            return
        db.add_all(
            Product(
                product_name=name,
                product_description=description,
                price=Decimal(price),
                category=category,
                image_url=_image_for(name),
            )
            for name, description, price, category in CATALOGUE
        )
        db.commit()
        print(f"seed_products: inserted {len(CATALOGUE)} products.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
