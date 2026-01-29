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

def validate_category(category):
    """"
    Validating category:

    Rules:
    - User can only choose allowed categories
    """
    allowed_category = ["Food", "Transport", "Rent", "Utilities"]

    if category not in allowed_category:
        raise ValidationError(f"Invalid category. Must be one of: {allowed_category}")
    
    
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

    allowed_type = ["M-Pesa", "Cash", "Bank"]

    if type not in allowed_type:
        raise ValidationError(f"Invalid type. Must be one of: {allowed_category}")
    
    
    logger.debug(f"Validated type: {type}")
    return type





