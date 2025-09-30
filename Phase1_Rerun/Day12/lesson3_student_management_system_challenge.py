class Student:
    total_students = 0

    def __init__ (self, name, student_id):
        self.name = name
        self.student_id = student_id
        self.grades = []

        Student.total_students += 1

    def add_grade(self, grade):
        if grade >= 0:
            self.grades.append(grade)
            return f"Grade {grade} added for {self.name}"
        return "Grade should be positive"

    def get_average(self):
        if not self.grades: #handles empty grades list
            return 0
        return sum(self.grades) / len(self.grades)

    def display_info(self):
        avg = self.get_average()
        return (f"Student: {self.name} (ID: {self.student_id})\n"
                f"Grades: {self.grades}\n"
                f"Average: {avg:.2f}\n"
                f"Total Students: {Student.total_students}")

student1 = Student("Alice", "S001")
student1.add_grade(85)
student1.add_grade(90)
student1.add_grade(78)
print(student1.get_average())  # Should print 84.33

student2 = Student("Bob", "S002")  # total_students becomes 2

print(student1.display_info())

