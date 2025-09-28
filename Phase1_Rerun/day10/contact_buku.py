contacts = []
next_id = 1

while True:
    print("\n=== CONTACT BOOK ===")
    print("1. Add Contact.")
    print("2. View All Contacts")
    print("3. Search Contacts")
    print("4. Delete Contacts")
    print("5. Exit")
    
    choice = input("Choose option (1-5)")

    if choice == "1":
        name = input("Enter name: ")
        number = input("Enter phone number: ")
        email = input("Enter Email: ")
    
        contacts.append({
            "id": next_id,
            "name": name,
            "number": number,
            "email": email
        })
        next_id += 1
        print("Contact Added")
    
    elif choice == "2":
        #View all contacts
        print("\n=== ALL CONTACTS ===")
        for contact in contacts:
            print(f"ID: {contact['id']} | {contact['name']} | {contact['number']} | {contact['email']}")
    
    elif choice == "3":
        term = input("Search for: ").lower()
        print("\n=== SEARCH CONTACTS ===")
        for contact in contacts:
            if term in contact["name"].lower() or term in contact["number"]:
                print(f"ID: {contact['id']} | {contact['name']} | {contact['number']} | {contact['email']}")

    elif choice == "4":
        #Delete Contact
        for contact in contacts:
            print(f"ID: {contact['id']} | {contact['name']} | {contact['number']} | {contact['email']}") 
        contact_id = int(input("Enter contact ID to delete: "))
        for i in range(len(contacts)):
            if contacts[i]["id"] == contact_id:
                removed = contacts.pop(i)
                print(f"Deleted: {removed['name']}")
        else:
            print("Contact not found")

    elif choice == "5":
        print("Goodbye")
        break

    else:
        print("Invalid Choice")
 
