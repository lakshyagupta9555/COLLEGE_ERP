from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    credits = models.IntegerField(default=3)
    is_lab = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    phone = models.CharField(max_length=15)
    subjects = models.ManyToManyField(Subject, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    address = models.TextField()
    
    def __str__(self):
        return f"{self.roll_number} - {self.user.get_full_name()}"
    
    def calculate_sgpa(self):
        enrollments = SubjectEnrollment.objects.filter(student=self, subject__semester=self.semester)
        total_credits = 0
        weighted_sum = 0
        
        for enrollment in enrollments:
            if enrollment.total_marks is not None:
                grade_point = self.get_grade_point(enrollment.total_marks)
                total_credits += enrollment.subject.credits
                weighted_sum += grade_point * enrollment.subject.credits
        
        return round(weighted_sum / total_credits, 2) if total_credits > 0 else 0
    
    def calculate_cgpa(self):
        enrollments = SubjectEnrollment.objects.filter(student=self, subject__semester__lte=self.semester)
        total_credits = 0
        weighted_sum = 0
        
        for enrollment in enrollments:
            if enrollment.total_marks is not None:
                grade_point = self.get_grade_point(enrollment.total_marks)
                total_credits += enrollment.subject.credits
                weighted_sum += grade_point * enrollment.subject.credits
        
        return round(weighted_sum / total_credits, 2) if total_credits > 0 else 0
    
    @staticmethod
    def get_grade_point(marks):
        if marks >= 90: return 10
        elif marks >= 80: return 9
        elif marks >= 70: return 8
        elif marks >= 60: return 7
        elif marks >= 50: return 6
        elif marks >= 40: return 5
        else: return 0

class SubjectEnrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    
    # Internal Marks (Theory)
    mid1_marks = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(20)])
    mid2_marks = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(20)])
    put_marks = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(20)])
    
    # Internal Marks (Practical for lab subjects)
    practical_marks = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(40)])
    
    # External Marks (Student can edit)
    external_marks = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Total calculation
    total_marks = models.FloatField(null=True, blank=True)
    
    class Meta:
        unique_together = ('student', 'subject')
    
    def calculate_internal(self):
        if self.subject.is_lab:
            return (self.practical_marks or 0)
        else:
            return (self.mid1_marks or 0) + (self.mid2_marks or 0) + (self.put_marks or 0)
    
    def save(self, *args, **kwargs):
        if self.external_marks is not None:
            internal = self.calculate_internal()
            self.total_marks = internal + self.external_marks
        super().save(*args, **kwargs)

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=True)
    marked_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('student', 'subject', 'date')
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.subject.code} - {self.date}"

class Notice(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    semester = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class Resume(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    resume_file = models.FileField(upload_to='resumes/')
    ats_score = models.FloatField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.roll_number} - Resume"