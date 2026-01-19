class Employee:

    def __init__(self, first_name, last_name, salary):
        self.first_name = first_name
        self.last_name = last_name
        self._salary = salary # Private variable

    @property
    def full_name(self):
        """Computed property - not stored, calculated on access"""
        return f"{self.first_name} {self.last_name}"

    @property
    def salary(self):
        """Protected access to salary"""
        return self._salary


    @salary.setter
    def salary(self, value):
        """Validate salary before setting"""
        if value < 0:
            raise ValueError("Salary cannot be negative!")
        if value > 1000000:
            print("⚠️  Warning: Very high salary!")
        self._salary = value
   
    @salary.deleter
    def salary(self):
        """Delete salary (set to 0)"""
        print(f"Deleting salary for {self.full_name}")
        self._salary = 0

