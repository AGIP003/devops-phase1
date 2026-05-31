"""Input Validation"""

from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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
        amount = float(amount)
    except (ValueError, TypeError):
        raise ValidationError(f"Amount must be a number, you wrote: {amount}")
    
    if amount <= 0:
        raise ValidationError(f"Amount must be positive, you wrote{amount}")
    
    if not (amount * 100).is_integer():
        raise ValidationError(f"Amount cannot have more than 2 decimal places")
    
    logger.debug(f"Validated Amount: {amount}")
    return amount

def validate_category(txn_type, category):
    """
    Validating category that is allowed for the given transaction type:

    Rules:
    - User can only choose allowed categories
    """
    clean_type = str(txn_type or "").strip().lower()
    clean_cat = str(category or "").strip().lower()
    allowed_pairs = {
        'income' : ["salary", "business", "freelance", "loan", "investments", "gifts", "debts paid", "other income"],
        'expense' : ["rent", "utilities", "food", "transport", "groceries", "loan", "airtime", "medical", "subscriptions", "entertainment", "electricity", "education", "vacations", "tools/software", "personal care", "taxes", "black tax", "other expense"]
    }
    
    allowed_for_type = allowed_pairs.get(clean_type, [])
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
    if not date_str:
        return datetime.now().strftime('%Y-%m-%d')
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValidationError(
            f"Invalid date format. Use YYYY-MM-DD, got: {date_str}"
        )
    
    if date > datetime.now():
        raise ValidationError(f"Date cannot be in the future: {date_str}")
    
    logger.debug(f"Validated date: {date_str}")
    return date_str

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



