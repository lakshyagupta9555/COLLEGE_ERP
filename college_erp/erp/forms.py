from django import forms
from .models import *

class StudentForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = Student
        fields = ['roll_number', 'department', 'degree', 'section', 'semester', 'phone', 'date_of_birth', 'address']
        widgets = {
            'degree': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'section': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg', 'placeholder': 'e.g. A'}),
            'roll_number': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'department': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'semester': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg', 'min': 1, 'max': 8}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg', 'rows': 3}),
        }

class TeacherForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = Teacher
        fields = ['employee_id', 'department', 'phone', 'subjects']

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'subject', 'date', 'is_present']

class InternalMarksForm(forms.ModelForm):
    class Meta:
        model = SubjectEnrollment
        fields = ['mid1_marks', 'mid2_marks', 'put_marks', 'practical_marks']

class ExternalMarksForm(forms.ModelForm):
    class Meta:
        model = SubjectEnrollment
        fields = ['external_marks']

class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['title', 'content', 'department', 'semester']

class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        # Expose resume file and academic percentages
        fields = ['resume_file', 'tenth_percentage', 'twelfth_percentage', 'job_description']
        widgets = {
            'tenth_percentage': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg', 'step': '0.01', 'min': 0, 'max': 100}),
            'twelfth_percentage': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg', 'step': '0.01', 'min': 0, 'max': 100}),
            'job_description': forms.Textarea(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg', 'rows': 4, 'placeholder': 'Paste job description or key requirements here to analyze ATS match.'}),
        }


class ExamForm(forms.ModelForm):
    start_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}))
    end_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}))

    class Meta:
        model = Exam
        fields = ['title', 'description', 'start_time', 'end_time', 'proctored']


class ExamQuestionForm(forms.ModelForm):
    # For MCQ questions allow entering choices as newline-separated text
    choices_text = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg', 'rows': 3}), help_text='Enter one choice per line for MCQ')

    class Meta:
        model = ExamQuestion
        fields = ['text', 'question_type', 'choices_text', 'correct_answer', 'marks']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg', 'rows': 3}),
            'question_type': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'correct_answer': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'}),
            'marks': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg', 'step': '0.5'}),
        }

    def clean(self):
        cleaned = super().clean()
        qtype = cleaned.get('question_type')
        choices_text = cleaned.get('choices_text')
        correct = cleaned.get('correct_answer')
        if qtype == 'mcq':
            if not choices_text:
                raise forms.ValidationError('MCQ questions require choices (one per line).')
            choices = [c.strip() for c in choices_text.splitlines() if c.strip()]
            if not choices:
                raise forms.ValidationError('Provide at least one choice for MCQ.')
            if correct and correct.strip() not in choices:
                raise forms.ValidationError('Correct answer must match one of the choices.')
            cleaned['_parsed_choices'] = choices
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        parsed = self.cleaned_data.get('_parsed_choices')
        if parsed is not None:
            instance.choices = parsed
        if commit:
            instance.save()
        return instance


from .models import Degree


class DegreeForm(forms.ModelForm):
    class Meta:
        model = Degree
        fields = ['name', 'code', 'university_name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-700 rounded-lg bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'code': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-700 rounded-lg bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'university_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-700 rounded-lg bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
        }



class SemesterPerformanceForm(forms.ModelForm):
    class Meta:
        model = SemesterPerformance
        fields = ['semester', 'sgpa']
        widgets = {
            'semester': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg', 'min': 1, 'max': 8}),
            'sgpa': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg', 'step': '0.01', 'min': 0, 'max': 10}),
        }

class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = ['degree', 'section',
                  'lecture1', 'lecture1_subject',
                  'lecture2', 'lecture2_subject',
                  'lecture3', 'lecture3_subject',
                  'lecture4', 'lecture4_subject',
                  'lecture5', 'lecture5_subject',
                  'lecture6', 'lecture6_subject',
                  'lecture7', 'lecture7_subject',
                  'lunch']
        widgets = {
            'degree': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'section': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-700 rounded-lg bg-gray-800 text-white', 'placeholder': 'e.g. A'}),
            'lecture1': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'lecture1_subject': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'lecture2': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'lecture2_subject': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'lecture3': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'lecture3_subject': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'lecture4': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'lecture4_subject': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'lecture5': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'lecture5_subject': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'lecture6': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'lecture6_subject': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'lecture7': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'lecture7_subject': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
            'lunch': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-4 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white'}),
        }
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'code': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'})
        }

class SubjectForm(forms.ModelForm):
    SEMESTER_CHOICES = [(i, f'Semester {i}') for i in range(1, 9)]
    
    semester = forms.ChoiceField(
        choices=SEMESTER_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'})
    )
    
    class Meta:
        model = Subject
        fields = ['name', 'code', 'semester', 'department', 'credits', 'is_lab']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'code': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'department': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'credits': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'is_lab': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 rounded focus:ring-blue-500'})
        }

class FeesForm(forms.ModelForm):
    class Meta:
        model = Fees
        fields = ['student', 'title', 'amount', 'fine', 'rewards']
        widgets = {
            'student': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'title': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'step': '0.01'}),
            'fine': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'step': '0.01'}),
            'rewards': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'step': '0.01'}),
        }

class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = FeePayment
        fields = ['amount', 'transaction_id', 'payment_method', 'remarks']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'step': '0.01'}),
            'transaction_id': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'placeholder': 'Leave empty for auto-generation'}),
            'payment_method': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'remarks': forms.Textarea(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'rows': 3}),
        }


class StudyMaterialForm(forms.ModelForm):
    class Meta:
        model = StudyMaterial
        fields = ['title', 'description', 'subject', 'section', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'rows': 3}),
            'subject': forms.Select(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
            'section': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500', 'placeholder': 'Leave blank for all sections'}),
            'file': forms.FileInput(attrs={'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'}),
        }

