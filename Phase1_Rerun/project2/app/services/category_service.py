from sqlalchemy import select
from app.extensions import db
from app.models.category import Category

CATEGORY_ALIASES = {
    "food": "Food",
    "lunch": "Food",
    "supper": "Food",
    "breakfast": "Food",
    "mandazi": "Food",
    "transport": "Transport",
    "matatu": "Transport",
    "fare": "Transport",
    "uber": "Transport",
    "bolt": "Transport",
    "rent": "Rent",
    "house": "Rent",
    "electricity": "Utilities",
    "water": "Utilities",
    "tokens": "Utilities",
    "wifi": "Utilities",
    "airtime": "Airtime",
    "data": "Airtime",
    "salary": "Income",
    "freelance": "Income",
}


def normalize_category_name(raw: str | None) -> str:
    """Clean messy free text into a canonical category name."""
    if not raw:
        return "Other"
    key = raw.strip().lower()
    return CATEGORY_ALIASES.get(key, raw.strip().title())


def get_or_create_category(
    name: str,
    type: str,
    user_id: int | None = None
) -> Category:
    """
    Find an existing category by name, type and user, or create it.
    flush() gets the id without committing — caller controls the transaction.
    """
    clean_name = normalize_category_name(name)

    stmt = select(Category).where(
        Category.name == clean_name,
        Category.user_id == user_id,
        Category.type == type,
    )
    existing = db.session.execute(stmt).scalar_one_or_none()

    if existing:
        return existing

    new_category = Category(name=clean_name, type=type, user_id=user_id)
    db.session.add(new_category)
    db.session.flush()   # gets the id assigned without committing
    return new_category
