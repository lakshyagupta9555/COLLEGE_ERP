import os
import django
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()
from erp.models import Student, Timetable

for s in Student.objects.all():
    deg = s.degree.name if s.degree else None
    sec = s.section
    tt = None
    if s.degree and s.section:
        tt = Timetable.objects.filter(degree=s.degree, section__iexact=s.section).first()
    print(f'Student {s.roll_number} degree={deg} section={sec} -> timetable id={tt.id if tt else None}')
