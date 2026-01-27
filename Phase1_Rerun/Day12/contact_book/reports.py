"""
For generating summaries and analytics
"""
import logging

logger = logging.getLogger(__name__)

def group_by_email():
    pass

sacco_logs = [
    ("0722111222", 500), 
    ("0733444555", 1000), 
    ("0722111222", 250),    # Same user as the first one!
    ("0711000000", 50),  # CRITICAL ERROR: Negative amount
    ("0713678492", 100),           # Invalid user
    ("0733444555", 300),
    ("0723582739", 400)
]

def find_duplicate_phones(contacts):
    """Filter, find and extact duplicate numbers used by multiple contacts"""
    filtered = {} # filters which phone belongs to which names
    for name, details in contacts.items():
        phone = details.get('phone', "").strip()
        if not phone:
            logger.error(f"Warning {name} has no phone number saved")
            continue            
        filtered.append(name)
                
    duplicates = {
        phone: names
        for phone, names in filtered.items()
        if len(names) > 1
    }
    
    logger.debug(f"Filtered {len(filtered)} duplicates")
    return duplicates

numbers = find_duplicate_phones((sacco_logs))
print (numbers)