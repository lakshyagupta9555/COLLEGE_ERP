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


class Degree(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, blank=True)
    # University or awarding body for the degree (optional)
    university_name = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name


class Timetable(models.Model):
    """Simple daily timetable per degree + section + semester. Stores 7 lecture times and one lunch time."""
    degree = models.ForeignKey(Degree, on_delete=models.CASCADE, null=True, blank=True)
    section = models.CharField(max_length=10)
    semester = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)],
        null=True,
        blank=True,
        help_text='Semester for which this timetable is applicable'
    )
    lecture1 = models.TimeField(null=True, blank=True)
    lecture2 = models.TimeField(null=True, blank=True)
    lecture3 = models.TimeField(null=True, blank=True)
    lecture4 = models.TimeField(null=True, blank=True)
    lecture5 = models.TimeField(null=True, blank=True)
    lecture6 = models.TimeField(null=True, blank=True)
    lecture7 = models.TimeField(null=True, blank=True)
    lunch = models.TimeField(null=True, blank=True)
    # Associate subjects to each lecture (optional)
    lecture1_subject = models.ForeignKey('Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_lecture1')
    lecture2_subject = models.ForeignKey('Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_lecture2')
    lecture3_subject = models.ForeignKey('Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_lecture3')
    lecture4_subject = models.ForeignKey('Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_lecture4')
    lecture5_subject = models.ForeignKey('Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_lecture5')
    lecture6_subject = models.ForeignKey('Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_lecture6')
    lecture7_subject = models.ForeignKey('Subject', on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_lecture7')
    updated_at = models.DateTimeField(auto_now=True)
    # comma-separated active days (e.g. 'mon,tue,wed') to allow variable weekly schedules
    active_days = models.CharField(max_length=100, blank=True, default='mon,tue,wed,thu,fri,sat')

    class Meta:
        unique_together = ('degree', 'section', 'semester')

    def __str__(self):
        deg = self.degree.name if self.degree else 'General'
        sem_str = f' - Sem {self.semester}' if self.semester else ''
        return f"{deg} - Section {self.section}{sem_str}"

    def get_active_days_list(self):
        if not self.active_days:
            return []
        return [d for d in self.active_days.split(',') if d]


class TimetableSlot(models.Model):
    DAYS = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
    ]
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='slots')
    day = models.CharField(max_length=3, choices=DAYS)
    lecture_number = models.IntegerField()  # 1..7
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('timetable', 'day', 'lecture_number')

    def __str__(self):
        return f"{self.get_day_display()} L{self.lecture_number} - {self.subject or '-'}"

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
    # Academic program (e.g., B.Tech, B.Sc). Optional - FK to Degree.
    degree = models.ForeignKey('Degree', on_delete=models.SET_NULL, null=True, blank=True)
    # Section allocated by teachers (e.g., A, B, C)
    section = models.CharField(max_length=10, null=True, blank=True)
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
    # mid1 and mid2 are out of 30 each, PUT is out of 70. These are later summarised/scaled to a 30-point internal total.
    mid1_marks = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(30)])
    mid2_marks = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(30)])
    put_marks = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(70)])
    
    # Internal Marks (Practical for lab subjects)
    practical_marks = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(40)])
    
    # External Marks (Student can edit) - now out of 70
    external_marks = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(70)])
    
    # Total calculation
    total_marks = models.FloatField(null=True, blank=True)
    
    class Meta:
        unique_together = ('student', 'subject')
    
    def calculate_internal(self):
        if self.subject.is_lab:
            # For lab subjects we keep practical marks (assumed already on the correct scale)
            return (self.practical_marks or 0)
        else:
            # For theory subjects: mid1 (30) + mid2 (30) + put (70) => raw max 130
            # We need to summarise/scale this raw internal total to be out of 30.
            raw = (self.mid1_marks or 0) + (self.mid2_marks or 0) + (self.put_marks or 0)
            max_raw = 30 + 30 + 70  # 130
            if max_raw <= 0:
                return 0
            scaled = (raw / max_raw) * 30.0
            return round(scaled, 2)
    
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
    # Single resume file (previously split into tech/non_tech)
    resume_file = models.FileField(upload_to='resumes/', null=True, blank=True)
    ats_score = models.FloatField(null=True, blank=True)
    # Optional job description text entered by the student for ATS matching
    job_description = models.TextField(null=True, blank=True)
    # Academic percentages for placement filtering
    tenth_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    twelfth_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.roll_number} - Resume"


class Exam(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    proctored = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"


class ExamQuestion(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('text', 'Short Answer'),
    ]
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='mcq')
    # For MCQ store choices as a list of strings in JSONField, e.g. ["A","B","C"]
    choices = models.JSONField(null=True, blank=True)
    # For MCQ store correct answer as the value matching one entry in choices
    correct_answer = models.CharField(max_length=500, null=True, blank=True)
    marks = models.FloatField(default=1.0)

    def __str__(self):
        return f"Q{self.id} - {self.exam.title}"


class ExamAttempt(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    answers = models.JSONField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    is_submitted = models.BooleanField(default=False)
    # Proctoring events captured from client (focus/blur, fullscreen exits, etc.)
    proctor_log = models.TextField(blank=True)

    class Meta:
        unique_together = ('exam', 'student')

    def __str__(self):
        return f"{self.student.roll_number} - {self.exam.title}"


class SemesterPerformance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='semester_performances')
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    sgpa = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'semester')
        ordering = ['semester']

    def __str__(self):
        return f"{self.student.roll_number} - Sem {self.semester}: {self.sgpa}"

class Fees(models.Model):
    TITLE_CHOICES = [
        ('tuition', 'Tuition Fee'),
        ('library', 'Library Fee'),
        ('lab', 'Lab Fee'),
        ('infrastructure', 'Infrastructure Fee'),
        ('examination', 'Examination Fee'),
        ('sports', 'Sports Fee'),
        ('hostel', 'Hostel Fee'),
        ('other', 'Other Fee'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fees')
    title = models.CharField(max_length=50, choices=TITLE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    fine = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    rewards = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    allocated_on = models.DateTimeField(auto_now_add=True)
    allocated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='allocated_fees')
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_fees')
    verified_on = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('student', 'title')
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.get_title_display()}"
    
    @property
    def total_amount(self):
        return self.amount + self.fine - self.rewards
    
    @property
    def amount_paid(self):
        payments = FeePayment.objects.filter(fee=self)
        return sum(p.amount for p in payments)
    
    @property
    def amount_remaining(self):
        return max(0, self.total_amount - self.amount_paid)

class FeePayment(models.Model):
    fee = models.ForeignKey(Fees, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    paid_on = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('cheque', 'Cheque'),
            ('draft', 'Draft'),
            ('online', 'Online'),
            ('cash', 'Cash'),
        ],
        default='online'
    )
    remarks = models.TextField(blank=True)
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.fee.student.roll_number}"


class ImportLog(models.Model):
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255, blank=True)
    created_count = models.IntegerField(default=0)
    updated_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    errors_preview = models.TextField(blank=True)

    def __str__(self):
        return f"Import {self.uploaded_at.strftime('%Y-%m-%d %H:%M')} by {self.uploaded_by}"


class StudyMaterial(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='study_materials')
    section = models.CharField(max_length=10, blank=True, help_text="Leave blank for all sections")
    file = models.FileField(upload_to='study_materials/')
    uploaded_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        section_str = f" - Section {self.section}" if self.section else " - All Sections"
        return f"{self.subject.code}: {self.title}{section_str}" 