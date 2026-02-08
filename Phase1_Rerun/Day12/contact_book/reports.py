"""
For generating summaries and analytics
"""
import logging

logger = logging.getLogger(__name__)

def group_by_email(contacts):
    """Group contacts through emails"""
    grouped_emails = {}
    for name, details in contacts.items():
        #Normalization
        email = details.get('email', "").strip().lower().replace(" ", "")
        if not email:
            logger.error(f"Warning!! Missing email for contact: {name}")
            continue

        grouped_emails.setdefault(email, []).append(name)
    logger.debug(f"Grouped{len(grouped_emails)} emails")
    return grouped_emails


def find_duplicate_phones(contacts):
    """Filter, find and extact duplicate numbers used by multiple contacts"""
    filtered = {} # filters which phone belongs to which names
    for name, details in contacts.items():
        phone = details.get('phone', "").strip()
        if not phone:
            logger.error(f"Warning missing phone number for: {name}")
            continue            
        filtered.setdefault(phone, []).append(name)
                
    duplicates = {
        phone: names
        for phone, names in filtered.items()
        if len(names) > 1
    }
    
    logger.debug(f"Filtered {len(duplicates)} duplicates")
    return duplicates

def group_by_number(contacts):
    """Filter names by numbers"""
    grouped_numbers = {}
    for name, details in contacts.items():
        phone = details.get('phone', "").strip()
        if not phone:
            logger.error(f"Warning!! Missing phone number for: {name}")
            continue            
        grouped_numbers.setdefault(phone, []).append(name)
    
    logger.debug(f"Grouped{len(grouped_numbers)} emails")
    return grouped_numbers

def generate_summary(contacts):
    """Generate comprehensive summary"""

    #Total contacts
    total_contacts = len(contacts)
    #Contacts with emails
    contacts_with_emails = group_by_email(contacts)
    #contacts with phone
    contacts_with_phone = group_by_number(contacts)

    #Unique phone numbers
    unique_email_count = 0
    shared_email_count = 0
    unique_phone_count = 0
    shared_phone_count = 0
    shared_email_details = {}
    shared_phone_details = {}
    for phone, names in contacts_with_phone.items():
        if len(names) == 1:
            unique_phone_count += 1
        elif len(names) > 1:
            shared_phone_details[phone] = names
            shared_phone_count += 1
        else:
            logger.error (f"Contact with number: {phone} has not been saved!!")
            continue

    #Shared emails details
    for emails, names in contacts_with_emails.items():
        if len(names) > 1:
            shared_email_details[emails] = names
            shared_email_count += 1
        #Unique emails
        elif len(names) == 1:
            unique_email_count += 1
        else: 
            logger.error (f"Contact with {emails} has not been saved!!")
            continue
    
    #Shared emails(details)
    #Shared phone numbers(details)

    return {
        'Total Contacts' : total_contacts,
        'Contacts with emails' : len(contacts_with_emails),
        'Contacts with phone numbers': len(contacts_with_phone),
        'Contacts with shared phone numbers': shared_phone_count,
        'Contacts with unique phone numbers': unique_phone_count,
        'Contacts with shared emails': shared_email_count,
        'Contacts with unique emails': unique_email_count,
        'Shared emails(details) list': shared_email_details,
        'Shared phone numbers(details) list': shared_phone_details
    }