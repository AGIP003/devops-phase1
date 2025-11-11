class Employee:
    def __init__(self, name, emp_id, base_salary):
        self.name = name
        self.emp_id = emp_id
        self.base_salary = base_salary

    def calculate_pay(self):
        return self.base_salary

class Manager(Employee):
    def __init__(self, name, emp_id, base_salary, department, team_size, bonus):
        super().__init__(name, emp_id, base_salary)
        self.department = department
        self.team_size = team_size
        self.bonus = bonus

    def calculate_pay(self):
        return self.base_salary + self.bonus

class  Developer(Employee):
    def __init__(self, name, emp_id, base_salary, programming_language, projects):
        super().__init__(name, emp_id, base_salary)
        self.programming_language = programming_language
        self.projects = projects

    def calculate_pay(self):
        projects_pay = self.projects * 50000
        return self.base_salary + projects_pay

class Intern(Employee):
    def __init__(self, name, emp_id, base_salary, university, hourly_rate):
        super().__init__(name, emp_id, base_salary)
        self.university = university
        self.hourly_rate = hourly_rate

    def calculate_pay(self):
        total_hourly_pay = self.hourly_rate * 200

        return self.base_salary + total_hourly_pay

employees = [
    Manager("Vee", "M001", 800000, "IT", 20, 100000),
    Developer("Jay", "D004", 80000, "Python", 20),
    Intern("Loki", "I003", 30000, "JKUAT", 500)
]

total = 0
for emp in employees:
    pay = emp.calculate_pay()
    print(f"{emp.name}: kshs{pay:,}")
    total += pay

print(f"TOTAL: kshs{total:,}")
