from django.core.management.base import BaseCommand
from erp.models import Student
from erp.utils import auto_enroll_student_subjects


class Command(BaseCommand):
    help = 'Automatically enrolls all students in subjects based on their department and semester'

    def add_arguments(self, parser):
        parser.add_argument(
            '--semester',
            type=int,
            help='Enroll only students in a specific semester',
        )
        parser.add_argument(
            '--department',
            type=str,
            help='Enroll only students in a specific department (use department code)',
        )

    def handle(self, *args, **options):
        semester = options.get('semester')
        department_code = options.get('department')
        
        # Build query
        students = Student.objects.all()
        
        if semester:
            students = students.filter(semester=semester)
            
        if department_code:
            students = students.filter(department__code=department_code)
        
        if not students.exists():
            self.stdout.write(self.style.WARNING('No students found matching the criteria'))
            return
        
        total_created = 0
        total_updated = 0
        total_students = 0
        
        self.stdout.write(f'Processing {students.count()} students...')
        
        for student in students:
            if student.department and student.semester:
                created, updated = auto_enroll_student_subjects(student)
                total_created += created
                total_updated += updated
                total_students += 1
                
                self.stdout.write(
                    f'  {student.roll_number}: {created} new enrollments, {updated} updated'
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Skipping {student.roll_number}: Missing department or semester'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Processed {total_students} students'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'  - {total_created} new enrollments created'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'  - {total_updated} enrollments updated'
            )
        )
