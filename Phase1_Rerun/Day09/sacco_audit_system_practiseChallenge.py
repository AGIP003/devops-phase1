import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s -%(message)s" # WHEN | HOW SERIOUS | WHICH ROOM | WHAT HAPPENED 
)

logger = logging.getLogger(__name__)

sacco_logs = [
    ("0722-111-222", 500), 
    ("0733 444 555", 1000), 
    ("0722111222", 250),    # Same user as the first one!
    ("0711-000-000", 50),  # CRITICAL ERROR: Negative amount
    ("None", 100),           # Invalid user
    ("0733 444 555", 300),
    ("254 723582739", 400)
]
"""Counting how many times a user appears and group their transaction amounts."""

def clean_and_audit(logs):
    #FREQUENCY COUNTING: How many times does a user show up?
    user_activity_count = {} 
    
    # GROUPING: What are their total transactions?
    user_transactions = {}
    for raw_phone, amount in logs:
        if amount <= 0:
            raise ValueError(f"CRITICAL ERROR: {amount} for {raw_phone} is negative!!")
        
        #Normalization
        clean_phone = str(raw_phone).strip().replace("-", "").replace(" ", "") 
        if clean_phone.startswith("254"):
            clean_phone = "0" + clean_phone[3:]
        elif clean_phone in ["None", "", "unknown"]:
            logger.warning(f"Skipping invalid user data: {raw_phone}")
            continue
        
        #if clean_phone in user_activity_count:
        #    current_val = user_activity_count[clean_phone]
        #else:
        #    current_val = 0

        #user_activity_count[clean_phone] = current_val + 1


        user_activity_count[clean_phone] = user_activity_count.get(clean_phone, 0) + 1

        user_transactions.setdefault(clean_phone, []).append(amount)
    
    return user_activity_count, user_transactions

try:
    counts, details = clean_and_audit(sacco_logs)
    print("User Activity", counts)
    print("User Details", details)
    print("AUDIT SUCCESSFUL")

except ValueError as e:
    print(f"AUDIT FAILED: {e}")

        

