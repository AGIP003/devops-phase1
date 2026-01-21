class ContactBook:
    def __init__(self):
        self.contacts = {}

    def add_contact(self, name, phone, email):
        """Adding a contact to the contactBook"""
        if name not in self.contacts:
            self.contacts[name] = []

        for contact in self.contacts[name]:
            if contact['phone'] == phone:
                raise ValueError ("Contact already saved")
            
        self.contacts[name].append({'phone':phone, 'email':email})
        return f"Added '{name}' to the contact book"
        
    def update_contact(self, name, phone, new_phone=None, new_email=None):
        """Updating a contact in the ContactBook"""
        if name not in self.contacts:
            raise ValueError ("Contact does not exist")
        
        for contact in self.contacts[name]:
            if contact['phone'] == phone:
                if new_phone:
                    contact['phone'] = new_phone
                if new_email:
                    contact['email'] = new_email
                
                return f"Updated '{name}' succesfully"
            
        raise ValueError ("Contact with this phone number not found!!")
        
    def delete_contact(self, name, phone):
        """Deleting Contacts from the contactbook"""
        if name not in self.contacts:
            raise ValueError ("Contact not found")
         
        for contact in self.contacts[name]:
            if contact['phone'] == phone:
                self.contacts[name].remove(contact)

                #Remove names if it has no contact
                if not self.contacts[name]:
                    del self.contacts[name]
        
                return f"Contact {name} deleted succesfully"
        
        raise ValueError ("Contact with this phone number not found!!")
        
    def search_contact(self, query, field="name"):
        """Searching contacts in the ContactBook"""
        results = []

        if field == "name":
            for name, contacts in self.contacts.items():
                if query.lower() in name.lower():
                    for contact in contacts:
                        results.append({'name': name, **contact})

        elif field == "phone":
            for name, contacts in self.contacts.items():
                for contact in contacts:
                    if query.replace(" ", "") in contact['phone'].replace(" ", ""):
                        results.append({'name': name, **contact})

        elif field == "email":
            for name, contacts in self.contacts.items():
                for contact in contacts:
                    if contact['email'] == query:
                        results.append({'name': name, **contact})
        return results
        
    def display_search_results(self, results):
        """To help display the searrch results better"""
        if not results:
            print("No matches found")
            return
        print(f"Found {len(results)} match(es):")

        for r in results:
            print(f" - {r.get('name','Unknown')}: {r['phone']} - {r['email']}")

    def display_all(self):
        """Displaying contacts in the ContactBook"""
        print("Contact:")
        for name, contacts in self.contacts.items():
            for contact in contacts:
                print(f" - {name}:  number - {contact['phone']}, email - {contact['email']}")

# Test Cases
book = ContactBook()
book.add_contact("Bob", "555-5678", "bob@email.com")
book.add_contact("Alice", "555-1234", "alice@email.com")
book.add_contact("Alice", "2312-32131", "Alice2@gmail.com")
book.add_contact("Vee", "211-23213", "weq12@gmail.com")
book.update_contact("Alice", phone="555-1234", new_phone="555-9999", new_email="alice555@gmail.com")
findings = book.search_contact("55 5", field="phone")
book.display_search_results(findings)
book.delete_contact("Bob", "555-5678")
book.display_all()

