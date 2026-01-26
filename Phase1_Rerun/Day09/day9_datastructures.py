#services = ["nginx", "mysql", "redis"]
#services.append("unix")
#services.remove("redis")
#print(services[0:3])
#server_info = ("10.0.0.5", 443)
#(ip, port) = server_info
#admins = {"jay", "mary", "paul"}
#devs = {"mary", "paul", "alex"}
#print(admins | devs)
#print(admins & devs)
#print(admins - devs)


data = [("user1", 500 ), ("user2", 1000), ("user1", 200)]
grouped_transactions = {}
"""If user is not in my records give them an empty list. Then handle the transaction."""
for user, amount in data:
    #Initialize if
    if user not in grouped_transactions:
        grouped_transactions[user] = []

    grouped_transactions[user].append(amount)

print(grouped_transactions)

def normalize_phone(raw_phone):
    """Removes spaces, dashes, and ensures it starts with 254 (Kenya)"""
    clean = str(raw_phone).strip().replace("-", "").replace(" ", "")
    if clean.startswith("0"):
        clean = "254"  + clean[1:]
    return clean

messy_inputs = [" 0712 345 678", "254-700-111-222 "]
for item in messy_inputs:
    clean_phone = normalize_phone(item)
    print(f"Clean phone numbers: {clean_phone}")


contact_registry = {"John": "0711237539"}

for name in contact_registry:
    phone = contact_registry[name]
    print(f"{name}: {phone}")