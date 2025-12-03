import os
import django
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()

from erp.models import Timetable, TimetableSlot, Degree

print('Timetables:')
for t in Timetable.objects.all():
    print(f'- ID={t.id} degree={t.degree} section={t.section} active_days={t.active_days}')
    print(f'  lecture times: {t.lecture1} {t.lecture2} {t.lecture3} {t.lecture4} {t.lecture5} {t.lecture6} {t.lecture7} lunch={t.lunch}')
    slots = TimetableSlot.objects.filter(timetable=t).order_by('day','lecture_number')
    print(f'  slots ({slots.count()}):')
    for s in slots:
        print(f'    {s.day} L{s.lecture_number}: {s.subject}')

print('Done')
