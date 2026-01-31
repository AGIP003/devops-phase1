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
    
    if round(amount, 2) != amount:
        raise ValidationError(f"Amount cannot have more than 2 decimal places")
    
    logger.debug(f"Validated Amount: {amount}")
    return amount

def validate_category(type, category):
    """"
    Validating category that is allowed for the given transaction type:

    Rules:
    - User can only choose allowed categories
    """
    allowed_pairs = {
        'income' : ["Salary", "Business", "Freelance", "Investments", "Gifts", "Other_Income"],
        'expense' : ["Rent", "Utilites", "Food", "Transport", "Medical", "Subscriptions", "Entertainment", "Education", "Vacations", "tools/software", "personal_care", "taxes", "black_tax", "other_expense"]
    }
    
    if category not in allowed_pairs.get(type, []):
        valid_categories = allowed_pairs.get(type, [])
        raise ValidationError(f"Invalid category. Must be one of the listed categories")
    
    
    logger.debug(f"Validated category: {category}")
    return category

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
    
    description = str(description).strip()

    if len(description) >= 200:
        raise ValidationError("The description is too long, (maximum characters is 200)")
    
    logger.debug(f"Validated description: {description}")
    return description

def validate_transaction_type(type):
    """
    Validation Types

    Rules:
    - User can only choose from the allowed or listed types
    """

    allowed_type = {"Income", "Expense"}

    if type not in allowed_type:
        raise ValidationError(f"Invalid type. Must be one of: {allowed_type}")
    
    
    logger.debug(f"Validated type: {type}")
    return type

def validate_payment_method(payment_method):
    """
    Validate payment methods

    Rules:
    - User can only choose from the allowed payment options
    """

    allowed_payment_method = ["Cash", "M-Pesa", "Bank", "Paypal", "Card"]

    if payment_method not in allowed_payment_method:
        raise ValidationError(f"Invalid payment method. Must be one of: {allowed_payment_method}")
    
    logger.debug(f"Validated payment method: {payment_method}")
    return payment_method




