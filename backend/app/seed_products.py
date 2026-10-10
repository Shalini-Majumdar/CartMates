"""Load a starter product catalogue into an empty database.

Run from the package directory (as docker-compose does):

    python seed_products.py

It only inserts when the products table is empty, so it is safe to run on
every start and never duplicates or overwrites products you have edited.
"""

from decimal import Decimal
from urllib.parse import quote_plus

from database import SessionLocal
from models.models import Product

# (name, description, price, category)
CATALOGUE = [
    # Snacks
    ("Salted Potato Chips", "Classic crispy potato chips, 150 g family pack.", "2.49", "Snacks"),
    ("Nacho Tortilla Chips", "Corn tortilla chips, great with salsa or dip, 200 g.", "2.99", "Snacks"),
    ("Butter Popcorn", "Microwave popcorn, pack of 3 bags.", "3.49", "Snacks"),
    ("Roasted Salted Peanuts", "Dry roasted peanuts, 300 g jar.", "3.99", "Snacks"),
    ("Trail Mix", "Nuts, raisins and chocolate chips, 400 g resealable bag.", "5.99", "Snacks"),
    ("Chocolate Chip Cookies", "Soft baked cookies, pack of 12.", "3.29", "Snacks"),
    ("Granola Bars", "Oats and honey bars, box of 10.", "4.49", "Snacks"),
    ("Milk Chocolate Bar", "Smooth milk chocolate, 100 g.", "1.99", "Snacks"),
    ("Tomato Salsa Dip", "Medium spicy salsa, 300 g jar.", "2.79", "Snacks"),
    # Beverages
    ("Sparkling Water 6-Pack", "Unflavoured sparkling mineral water, 6 x 500 ml.", "3.99", "Beverages"),
    ("Orange Juice", "100% orange juice, no added sugar, 1 L.", "3.49", "Beverages"),
    ("Cola 12-Pack", "Classic cola, 12 x 330 ml cans.", "6.99", "Beverages"),
    ("Green Tea Bags", "Pure green tea, box of 50 bags.", "4.29", "Beverages"),
    ("Ground Coffee", "Medium roast ground coffee, 250 g.", "6.49", "Beverages"),
    ("Bottled Water 24-Pack", "Still drinking water, 24 x 500 ml.", "5.49", "Beverages"),
    # Breakfast
    ("Whole Wheat Bread", "Sliced whole wheat loaf, 400 g.", "2.29", "Breakfast"),
    ("Free Range Eggs", "Dozen large free range eggs.", "4.19", "Breakfast"),
    ("Rolled Oats", "Whole grain rolled oats, 1 kg.", "3.19", "Breakfast"),
    ("Corn Flakes", "Crispy corn flakes cereal, 500 g.", "3.59", "Breakfast"),
    ("Strawberry Jam", "Strawberry fruit spread, 350 g jar.", "2.89", "Breakfast"),
    ("Peanut Butter", "Creamy peanut butter, 450 g jar.", "3.79", "Breakfast"),
    # Dairy
    ("Whole Milk", "Fresh whole milk, 1 L.", "1.49", "Dairy"),
    ("Greek Yogurt", "Plain Greek yogurt, 500 g tub.", "3.29", "Dairy"),
    ("Cheddar Cheese Block", "Mature cheddar, 200 g.", "3.99", "Dairy"),
    ("Salted Butter", "Salted butter, 250 g block.", "2.99", "Dairy"),
    # Fruits & Vegetables
    ("Bananas", "Bunch of 6 ripe bananas.", "1.89", "Fruits & Vegetables"),
    ("Red Apples", "Crisp red apples, 1 kg bag.", "3.49", "Fruits & Vegetables"),
    ("Baby Carrots", "Washed baby carrots, 500 g.", "1.99", "Fruits & Vegetables"),
    ("Cherry Tomatoes", "Sweet cherry tomatoes, 250 g punnet.", "2.49", "Fruits & Vegetables"),
    ("Mixed Salad Leaves", "Ready-to-eat salad mix, 200 g.", "2.29", "Fruits & Vegetables"),
    # Pantry
    ("Spaghetti", "Durum wheat spaghetti, 500 g.", "1.59", "Pantry"),
    ("Pasta Sauce", "Tomato and basil pasta sauce, 500 g jar.", "2.99", "Pantry"),
    ("Basmati Rice", "Long grain basmati rice, 1 kg.", "3.89", "Pantry"),
    ("Instant Noodles 5-Pack", "Chicken flavour instant noodles, 5 packs.", "2.49", "Pantry"),
    ("Baked Beans", "Baked beans in tomato sauce, 400 g can.", "1.29", "Pantry"),
    # Toiletries
    ("Toothpaste", "Fluoride toothpaste, mint, 100 ml.", "2.49", "Toiletries"),
    ("Toothbrush 2-Pack", "Medium bristle toothbrushes, pack of 2.", "3.29", "Toiletries"),
    ("Shampoo", "Daily care shampoo for all hair types, 400 ml.", "4.99", "Toiletries"),
    ("Body Wash", "Moisturising body wash, 500 ml.", "4.49", "Toiletries"),
    ("Deodorant", "48-hour roll-on deodorant, 50 ml.", "3.49", "Toiletries"),
    ("Hand Soap", "Liquid hand soap with pump, 250 ml.", "1.99", "Toiletries"),
    # Household
    ("Toilet Paper 12-Roll", "Soft 3-ply toilet paper, 12 rolls.", "7.99", "Household"),
    ("Paper Towels 4-Roll", "Absorbent kitchen paper towels, 4 rolls.", "4.99", "Household"),
    ("Dish Soap", "Lemon dishwashing liquid, 750 ml.", "2.79", "Household"),
    ("Trash Bags", "Heavy duty 30 L trash bags, 40 count.", "5.49", "Household"),
    ("Disposable Plates", "Sturdy paper plates, pack of 50.", "4.29", "Household"),
    ("Disposable Cups", "Paper cups, 250 ml, pack of 50.", "3.79", "Household"),
    # Outdoor & Travel
    ("Sunscreen SPF 50", "Water resistant sunscreen lotion, 200 ml.", "8.99", "Outdoor & Travel"),
    ("Insect Repellent", "DEET-free insect repellent spray, 100 ml.", "6.49", "Outdoor & Travel"),
    ("LED Flashlight", "Compact LED flashlight with batteries.", "9.99", "Outdoor & Travel"),
    ("AA Batteries 8-Pack", "Long-lasting alkaline AA batteries.", "7.49", "Outdoor & Travel"),
    ("First Aid Kit", "Travel first aid kit, 40 pieces.", "12.99", "Outdoor & Travel"),
    ("Wet Wipes", "Fragrance-free wet wipes, 80 count.", "2.99", "Outdoor & Travel"),
]


def _image_for(name: str) -> str:
    return f"https://placehold.co/300x300?text={quote_plus(name)}"


def main() -> None:
    db = SessionLocal()
    try:
        if db.query(Product).first() is not None:
            print("seed_products: products already present, nothing to do.")
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
