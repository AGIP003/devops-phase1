class Student:
    
    total_students = 0
    
    
    def __init__(self, name, student_id):
        self.name = name
        self.student_id = student_id
        self.grades = []
        
        Student.total_students += 1

    def add_grade(self, grade):
        print(f"Student:  {self.name} ID: {self.student_id}  grade: {grade}")
        self.grades.append(grade)

    def get_average(self):
        if not self.grades:
            return 0
        else:
            return sum(self.grades) / len(self.grades)
 

    def display_info(self, grade):
        print(f"Student: {self.name}, ID: {self.student_id} Grade: {grade}")

student1 = Student("Alic", "S001")
student1.add_grade(85)
student1.add_grade(90)
student1.add_grade(78)
print(student1.get_average())
