import re
from difflib import SequenceMatcher


CATEGORIES = {
    "income": [
        "salary", "business", "freelance", "loan", "investments", "gifts",
        "debts paid", "other income",
    ],
    "expense": [
        "rent", "utilities", "food", "transport", "groceries", "loan",
        "airtime", "medical", "subscriptions", "entertainment", "electricity",
        "education", "vacations", "tools/software", "personal care", "taxes",
        "black tax", "other expense",
    ],
}

PAYMENT_METHODS = [
    "cash", "m-pesa", "airtel money", "t-kash", "equitel",
    "bank transfer", "debit card", "credit card", "paypal",
]

PAYMENT_ALIASES = {
    "mpesa": "m-pesa",
    "m pesa": "m-pesa",
    "airtel": "airtel money",
    "tkash": "t-kash",
    "t kash": "t-kash",
    "bank": "bank transfer",
    "transfer": "bank transfer",
    "debit": "debit card",
    "credit": "credit card",
}

CATEGORY_KEYWORDS = {
    "salary": ["salary", "payday", "wages"],
    "business": ["business", "sales", "shop"],
    "freelance": ["freelance", "client", "gig"],
    "investments": ["investment", "dividend", "interest"],
    "gifts": ["gift", "present"],
    "debts paid": ["debt repaid", "paid me back", "refund"],
    "rent": ["rent", "landlord"],
    "utilities": ["utility", "water bill", "internet bill"],
    "food": ["food", "lunch", "dinner", "breakfast", "meal", "restaurant"],
    "transport": ["transport", "matatu", "uber", "bolt", "taxi", "fare", "fuel"],
    "groceries": ["groceries", "supermarket", "shopping"],
    "airtime": ["airtime", "data bundle", "bundles"],
    "medical": ["medical", "hospital", "doctor", "pharmacy", "medicine"],
    "subscriptions": ["subscription", "netflix", "spotify"],
    "entertainment": ["entertainment", "movie", "cinema", "club"],
    "electricity": ["electricity", "tokens", "kplc"],
    "education": ["education", "school", "tuition", "books"],
    "vacations": ["vacation", "holiday", "trip"],
    "tools/software": ["software", "hosting", "domain", "tool"],
    "personal care": ["salon", "barber", "skincare", "personal care"],
    "taxes": ["tax", "kra"],
    "black tax": ["black tax", "family support"],
    "loan": ["loan"],
}

AMOUNT_PATTERN = re.compile(
    r"^\s*(?P<sign>-)?\s*(?:kes|ksh|kshs|\$|€|£)?\s*"
    r"(?P<amount>\d[\d,]*(?:\.\d{1,2})?)\s*",
    re.IGNORECASE,
)


class TransactionInputError(ValueError):
    pass


def normalize_payment_method(value):
    clean = re.sub(r"\s+", " ", str(value or "").strip().lower())
    clean = PAYMENT_ALIASES.get(clean, clean)
    return clean if clean in PAYMENT_METHODS else None


def parse_amount_and_description(text):
    match = AMOUNT_PATTERN.match(text or "")
    if not match:
        raise TransactionInputError(
            "Start with an amount, for example: /add 250 lunch"
        )

    amount = float(match.group("amount").replace(",", ""))
    if amount <= 0:
        raise TransactionInputError("Amount must be greater than zero.")
    if round(amount, 2) != amount:
        raise TransactionInputError("Amount can have at most two decimal places.")

    description = (text[match.end():] or "").strip(" ,-")
    if not description:
        raise TransactionInputError(
            "Add a description after the amount, for example: /add 250 lunch"
        )
    if len(description) > 200:
        raise TransactionInputError("Description must be 200 characters or fewer.")

    return amount, description, bool(match.group("sign"))


def extract_payment_method(description, default_payment_method):
    lower = description.lower()
    explicit_match = re.search(
        r"\b(?:via|using|by)\s+([a-z][a-z -]{1,30})\s*$",
        lower,
    )
    for alias, canonical in sorted(
        {**PAYMENT_ALIASES, **{item: item for item in PAYMENT_METHODS}}.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        if re.search(rf"\b(?:via|using|by)\s+{re.escape(alias)}\b", lower):
            return canonical, False, alias
    if explicit_match:
        return None, True, explicit_match.group(1).strip()
    return normalize_payment_method(default_payment_method) or "m-pesa", False, None


def category_candidates(description, aliases=None, forced_type=None):
    clean = re.sub(r"\s+", " ", description.strip().lower())
    aliases = {
        str(alias).strip().lower(): str(category).strip().lower()
        for alias, category in (aliases or {}).items()
    }

    categories = [
        (txn_type, category)
        for txn_type, values in CATEGORIES.items()
        if not forced_type or txn_type == forced_type
        for category in values
    ]

    scores = []
    words = set(re.findall(r"[a-z0-9]+", clean))
    for txn_type, category in categories:
        score = 0.0
        if category in clean:
            score = 1.0
        for alias, target in aliases.items():
            if target == category and alias in clean:
                score = max(score, 1.0)
        for keyword in CATEGORY_KEYWORDS.get(category, []):
            if keyword in clean:
                score = max(score, 0.96)
        for word in words:
            score = max(score, SequenceMatcher(None, word, category).ratio() * 0.78)
        scores.append((score, txn_type, category))

    scores.sort(reverse=True)
    return scores[:3]


def parse_transaction(text, preferences=None):
    preferences = preferences or {}
    amount, description, negative_amount = parse_amount_and_description(text)
    lower = description.lower()

    forced_type = None
    if negative_amount or re.search(r"\b(income|received|earned)\b", lower):
        forced_type = "income"
    elif re.search(r"\b(expense|spent|paid|bought)\b", lower):
        forced_type = "expense"

    explicit_category = None
    for txn_type, categories in CATEGORIES.items():
        for category in sorted(categories, key=len, reverse=True):
            if lower == category or lower.startswith(f"{category} "):
                explicit_category = category
                forced_type = forced_type or txn_type
                break
        if explicit_category:
            break

    if forced_type is None:
        aliases = preferences.get("category_aliases", {})
        for alias, category in aliases.items():
            if str(alias).strip().lower() in lower:
                for txn_type, categories in CATEGORIES.items():
                    if str(category).strip().lower() in categories:
                        forced_type = txn_type
                        break
            if forced_type:
                break

    candidates = category_candidates(
        description,
        preferences.get("category_aliases", {}),
        forced_type=forced_type or "expense",
    )
    if explicit_category:
        category = explicit_category
        txn_type = forced_type
        ambiguous = False
    elif candidates and candidates[0][0] >= 0.9:
        _, txn_type, category = candidates[0]
        ambiguous = (
            len(candidates) > 1
            and candidates[1][0] >= 0.9
            and candidates[1][2] != category
        )
    else:
        txn_type = forced_type or "expense"
        category = None
        ambiguous = True

    payment_method, invalid_payment, supplied_payment = extract_payment_method(
        description,
        preferences.get("default_payment_method"),
    )

    return {
        "amount": amount,
        "description": description.strip(),
        "type": txn_type,
        "category": category,
        "payment_method": payment_method,
        "invalid_payment": invalid_payment,
        "supplied_payment": supplied_payment,
        "candidates": [
            {"type": item_type, "category": item_category}
            for _, item_type, item_category in candidates
        ],
        "ambiguous": ambiguous,
    }
