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
        fields = ['roll_number', 'department', 'semester', 'phone', 'date_of_birth', 'address']

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
        fields = ['resume_file']

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