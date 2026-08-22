"""Input Validation"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)


ALLOWED_TRANSACTION_CATEGORIES = {
    "income": (
        "salary",
        "business",
        "freelance",
        "loan",
        "investments",
        "gifts",
        "debts paid",
        "other income",
    ),
    "expense": (
        "rent",
        "utilities",
        "food",
        "transport",
        "groceries",
        "loan",
        "airtime",
        "medical",
        "subscriptions",
        "entertainment",
        "electricity",
        "education",
        "vacations",
        "tools/software",
        "personal care",
        "taxes",
        "black tax",
        "other expense",
    ),
}

class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_amount(amount):
    """
    Validating transaction amount    
    
    Rules:
    - Must be a number
    - Must be positive
    - Maximum 2 dp.
    """

    try:
        decimal_amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(f"Amount must be a number, you wrote: {amount}")
    
    if not decimal_amount.is_finite():
        raise ValidationError("Amount must be a finite number")
    
    if decimal_amount <= 0:
        raise ValidationError(f"Amount must be positive, you wrote: {decimal_amount}")

    rounded_amount = decimal_amount.quantize(Decimal("0.01"))

    if decimal_amount != rounded_amount:
        raise ValidationError("Amount cannot have more than 2 decimal places")

    logger.debug(f"Validated Amount: {decimal_amount}")
    return decimal_amount

def validate_category(txn_type, category):
    """
    Validating category that is allowed for the given transaction type:

    Rules:
    - User can only choose allowed categories
    """
    clean_type = str(txn_type or "").strip().lower()
    clean_cat = str(category or "").strip().lower()
    allowed_for_type = ALLOWED_TRANSACTION_CATEGORIES.get(
        clean_type,
        (),
    )

    if clean_cat not in allowed_for_type:
        raise ValidationError(f"Invalid category {clean_cat}. Must be one of the listed categories")
    
    logger.debug(f"Validated category: {clean_cat}")
    return clean_cat

def validate_date(date_str):
    """
    Validate date string
    
    Rules:
    - Format: YYYY-MM-DD
    - Must be valid date
    - Cannot be in future
    """
    #Formatting date and returning a readable string    ``
    try:
        parsed_date = datetime.strptime(
            str(date_str),
            "%Y-%m-%d",
        ).date()
    except (ValueError, TypeError):
        raise ValidationError(
            f"Invalid date format. Use YYYY-MM-DD, got: {date_str}"
        )

    if parsed_date > date.today():
        raise ValidationError(f"Date cannot be in the future: {date_str}")

    return parsed_date

def validate_description(description):
    """
    Validate Description
    
    Rules:
    - Optional
    - Should not be more than 200 characters
    """

    if not description:
        return ""
    
    description = str(description).strip().lower()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              

    if len(description) > 200:
        raise ValidationError("The description is too long, (maximum characters is 200)")
    
    logger.debug(f"Validated description: {description}")
    return description 

def validate_transaction_type(txn_type):
    """
    Validation Types

    Rules:
    - User can only choose from the allowed or listed types
    """

    allowed_type = {"income", "expense"}
    clean_type = str(txn_type or "").strip().lower()

    if clean_type not in allowed_type:
        raise ValidationError(f"Invalid type. Must be one of: {allowed_type}")
    
    logger.debug(f"Validated type: {clean_type}")
    return clean_type

def validate_payment_method(payment_method):
    """
    Validate payment methods

    Rules:
    - User can only choose from the allowed payment options
    """

    allowed_payment_method = [
        "cash", "m-pesa", "airtel money", "t-kash", "equitel",
        "bank transfer", "debit card", "credit card", "paypal"
    ]
    clean_pm = str(payment_method or "").strip().lower()
    allowed_lower = [p.lower() for p in allowed_payment_method]
    if clean_pm not in allowed_lower:
        raise ValidationError(f"Invalid payment method. Must be one of: {allowed_payment_method}")
    
    logger.debug(f"Validated payment method: {clean_pm}")
    return clean_pm



