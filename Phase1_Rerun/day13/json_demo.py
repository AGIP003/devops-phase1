import json

print("="*60)
print("1. json.dumps() - Python → JSON String")
print("="*60)

person = {
    "name": "Alice",
    "age": 30,
    "city": "Nairobi",
    "skills":["Python", "Javascript"],
    "is_student": False
}

json_string = json.dumps(person)
print(f"Type: {type(json_string)}")
print(json_string)

#Pretty print
json_pretty = json.dumps(person, indent=2)
print("Pretty printed(json)\n")
print(json_pretty)


print("\n" + "="*60)
print("2. json.loads() - JSON String → Python")
print("="*60)


json_data = '{"name": "Bob", "age": 25, "city": "Mombasa"}'
python_dict = json.loads(json_data)
print(f"Type: {type(python_dict)}")
print(f"Name: {python_dict['name']}")
print(f"Age: {python_dict['age']}")


print("\n" + "="*60)
print("3. json.dump() - Python → JSON File")
print("="*60)

users = [
    {"id": 1, "name": "Alice", "email": "alice@email.com"},
    {"id": 2, "name": "Bob", "email": "bob@email.com"},
    {"id": 3, "name": "Charlie", "email": "charlie@email.com"}
]

with open('user.json', 'w') as f:
    json.dump(users, f, indent=2)

print("Saved to users.json")



print("\n" + "="*60)
print("4. json.load() - JSON File → Python")
print("="*60)


with open('user.json', 'r') as f:
    loaded_users = json.load(f)

print(f"Loaded {len(loaded_users)} users:")
for user in loaded_users:
    print(f" - {user['name']} ({user['email']})")
