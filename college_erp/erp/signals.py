from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Student
from .utils import auto_enroll_student_subjects


@receiver(post_save, sender=Student)
def enroll_student_in_subjects(sender, instance, created, **kwargs):
    """
    Signal to automatically enroll students in subjects when:
    1. A new student is created
    2. A student's semester or department is updated
    
    This ensures students are always enrolled in the correct subjects
    for their current semester and department.
    """
    # Only enroll if student has both department and semester set
    if instance.department and instance.semester:
        auto_enroll_student_subjects(instance)
