class Library:
    total_books = 0
    def __init__(self, library_name):
        self.library_name = library_name
        self.books = {}

    def add_book(self, title, author, copies):
        """Adding books to the Library"""
        if title in self.books:
            self.books[title]['copies'] += copies
        else:
            self.books[title] = {'author': author, 'copies': copies}

    def borrow_book(self, title):
        """Borrowing books from the library"""
        if title not in self.books:
            raise ValueError("The title does not exist!!")
        
        if self.books[title]['copies'] <= 0:
            raise ValueError(f"Not available, {self.books[title]['copies']} left")
        
        self.books[title]['copies'] -= 1
        return f" Borrowed '{title}'. {self.books[title]['copies']} copies left"
    
    def return_book(self, title):
        """Returning the borrowed boook from the library"""
        if title not in self.books:
            raise ValueError("Unknown book")
        
        self.books[title]['copies'] += 1
        return f" Returned '{title}'. {self.books[title]['copies']} copies in the library"


    def display_books(self):
        print(f"Library Name: {self.library_name}")
        print("Books:")
        for title, data in self.books.items():
            print(f" - {title} : Author - {data['author']},  Copies - {data['copies']}")


lib = Library("City Library")
lib.add_book("Python Basics", "John Doe", 3)
lib.add_book("Python Basics", "John Doe", 4)
lib.add_book("Flask Web", "Jane Smith", 2)
lib.borrow_book("Python Basics")
lib.display_books()