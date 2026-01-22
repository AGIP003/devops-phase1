import json
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s -%(message)s" # WHEN | HOW SERIOUS | WHICH ROOM | WHAT HAPPENED 
)

logger = logging.getLogger(__name__)

class ContactBook:
    def __init__(self, storage_file="contacts.json"):
        self.storage_file = storage_file
        self._ensure_file_exists()
        self.contacts = self.load_contacts()

    def _ensure_file_exists(self):
        """Check if file exists and create if it doesn't"""
        #Data Directory
        directory = os.path.dirname(self.storage_file)
        if directory:
            os.makedirs(directory, exist_ok=True)

        if not os.path.exists(self.storage_file):
            with open(self.storage_file, "w") as f:
                json.dump({}, f)
                logger.info(f"Created New storage file: {self.storage_file}")

    def load_contacts(self):
        """Load all Contacts"""
        try:
            with open(self.storage_file, "r") as f:
                contacts = json.load(f)
            logger.debug(f"Loaded {len(contacts)} contacts")
            return contacts
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e} ")
            return {}
        except Exception as e:
            logger.error(f"Failed to load: {e}")
            return {}


    def save_contacts(self):
        """Save all contacts"""
        try:
            with open(self.storage_file, "w") as f:
                json.dump(self.contacts, f, indent=4, sort_keys=True)
                logger.info(f"Saved {len(self.contacts)} successfully.")
            return True
        except Exception as e: 
            logger.error(f"Failed to save contacts: {e}")
            return False



    def add_contact(self, name, phone, email):
        """Adding a contact to the contactBook"""
        if name not in self.contacts:
            self.contacts[name] = []

        for contact in self.contacts[name]:
            if contact['phone'] == phone:
                raise ValueError ("Contact already saved")
            
        self.contacts[name].append({'phone':phone, 'email':email})

        self.save_contacts()
        logger.info(f"Added contact: {name} - {phone} - {email}")

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
                self.save_contacts()
                logger.info(f"Updated contact: {name}")
                return f"Updated '{name}' succesfully"
      
            raise ValueError ("Contact with this phone number not found!!")
    
        #self.save_contacts()
        #logger.info(f"Updated contact: {name}")
        #return f"Updated '{name}' succesfully"

        
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
                
                self.save_contacts()
                logger.info(f"Deleted contact: {name}")
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
book = ContactBook("data/contacts.json")
book.add_contact("Bob", "555-5678", "bob@email.com")
book.add_contact("Alice", "555-1234", "alice@email.com")
book.add_contact("Alice", "2312-32131", "Alice2@gmail.com")
book.add_contact("Vee", "211-23213", "weq12@gmail.com")
book.update_contact("Alice", phone="555-1234", new_phone="555-9999", new_email="alice555@gmail.com")
findings = book.search_contact("55 5", field="phone")
book.display_search_results(findings)
book.delete_contact("Bob", "555-5678")
book.display_all()

