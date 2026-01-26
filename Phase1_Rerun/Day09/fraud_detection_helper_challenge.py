phone_data = [(" 0722-111 ", 500), ("0722111", 1000)]
grouped_numbers = {}

def normalize_phone(raw_phone_data):
    clean = str(raw_phone_data).strip().replace("-","").replace(" ", "")
    return clean

#"""Group the amounts by phone number"""
#for phone_number, amount in phone_data:
#    clean_phone_data = normalize_phone(phone_number)
#    if  clean_phone_data not in grouped_numbers:
#        grouped_numbers[clean_phone_data] = []
#
#    grouped_numbers[clean_phone_data].append(amount)
#
#print(grouped_numbers)


#Challenge 2
"""Groups by amount instead of phone number"""

for phone_number, amount in phone_data:
    clean_phone_data = normalize_phone(phone_number)

    if amount not in grouped_numbers:
        grouped_numbers[amount] = []

    grouped_numbers[amount].append(phone_number)

#print(grouped_numbers)

#Challenge 3

raw_data = [
    ("0722-111-222", 500), 
    (" ", 100),            # Invalid
    ("0733 444 555", 1000), 
    ("None", 20),           # Invalid
    ("0711222333", 50)
]

transaction_ledger = {}

"""Grouping into a dictionary where the Keys are the "Status" (Clean or Invalid) and the Values are a list of the amounts."""

def normalize_transaction(raw_data_string):
    clean = str(raw_data_string).strip().replace("-", "").replace(" ", "")
    if clean in ["", "None"]:
        return "Invalid"
    else:
        return "Clean"


for phone_number, amount in raw_data:
    clean_transaction = normalize_transaction(phone_number)

    transaction_ledger.setdefault(clean_transaction, []).append(amount)

    #if status not in transaction_ledger:
    #    transaction_ledger[clean_transaction] = []
#
    #transaction_ledger[status].append(amount)

print(transaction_ledger)