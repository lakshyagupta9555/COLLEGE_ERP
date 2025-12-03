import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
import django
try:
    # Ensure project root is on sys.path so Django can import settings
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    django.setup()
except Exception as e:
    print('Django setup error:', e)
    sys.exit(1)
from django.template.loader import render_to_string

class DummyExam:
    def __init__(self):
        self.title = 'Sample Exam'
        self.description = 'This is a sample exam.'

class DummyQ:
    def __init__(self, id, text, qtype, choices, correct_answer, marks=1):
        self.id = id
        self.text = text
        self.question_type = qtype
        self.choices = choices
        self.correct_answer = correct_answer
        self.marks = marks

context = {
    'exam': DummyExam(),
    'questions': [DummyQ(1, 'What is 2+2?', 'mcq', ['2','3','4','5'], '4')],
    'attempt': None,
    'remaining_seconds': 120,
}

try:
    output = render_to_string('student/take_exam.html', context)
    print('Rendered template length:', len(output))
except Exception as e:
    print('Template render error:', repr(e))
    import traceback
    traceback.print_exc()
    sys.exit(2)

print('Success')
