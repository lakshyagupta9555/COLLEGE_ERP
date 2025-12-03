from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Avg, Count, Q
from datetime import datetime, timedelta
from .models import *
from .forms import *
from .utils import *
import os
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse

from django.contrib.admin.views.decorators import staff_member_required
from django.http import StreamingHttpResponse
import csv
import io
import zipfile
from django.utils.encoding import smart_str
from .forms import DegreeForm
from .models import Degree
from .models import Timetable
from .forms import TimetableForm
from .models import TimetableSlot

# ============ Authentication Views ============

def role_selection(request):
    """Landing page to select user role"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'role_selection.html')

def login_view(request):
    # If already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            # Check if there's a 'next' parameter
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'login.html')

def student_login(request):
    """Student-specific login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            # Check if user is a student
            try:
                if hasattr(user, 'student'):
                    login(request, user)
                    return redirect('student_dashboard')
                else:
                    messages.error(request, 'This account is not registered as a student.')
            except:
                messages.error(request, 'This account is not registered as a student.')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html', {'role': 'Student', 'role_icon': 'fa-user-graduate', 'role_color': 'blue'})

def teacher_login(request):
    """Teacher-specific login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            # Check if user is a teacher
            try:
                if hasattr(user, 'teacher'):
                    login(request, user)
                    return redirect('teacher_dashboard')
                else:
                    messages.error(request, 'This account is not registered as faculty.')
            except:
                messages.error(request, 'This account is not registered as faculty.')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html', {'role': 'Faculty', 'role_icon': 'fa-chalkboard-teacher', 'role_color': 'green'})

def admin_login(request):
    """Admin-specific login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            # Check if user is an admin
            if user.is_superuser:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'This account does not have admin privileges.')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html', {'role': 'Admin', 'role_icon': 'fa-user-shield', 'role_color': 'purple'})


def logout_view(request):
    logout(request)
    return redirect('role_selection')

@login_required(login_url='login')
def dashboard(request):
    user = request.user
    
    # Check user type and redirect accordingly
    if user.is_superuser:
        return redirect('admin_dashboard')
    
    try:
        if hasattr(user, 'teacher'):
            return redirect('teacher_dashboard')
        elif hasattr(user, 'student'):
            return redirect('student_dashboard')
    except:
        pass
    
    # If no profile exists, logout and show error
    logout(request)
    messages.error(request, 'No profile associated with this account. Please contact administrator.')
    return redirect('login')
# ============ Admin Views ============

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    context = {
        'total_students': Student.objects.count(),
        'total_teachers': Teacher.objects.count(),
        'total_departments': Department.objects.count(),
        'total_subjects': Subject.objects.count(),
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
def admin_add_student(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            student = form.save(commit=False)
            student.user = user
            student.save()
            messages.success(request, 'Student added successfully')
            return redirect('admin_students')
    else:
        form = StudentForm()
    
    return render(request, 'admin/add_student.html', {'form': form})

@login_required
def admin_add_teacher(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            teacher = form.save(commit=False)
            teacher.user = user
            teacher.save()
            form.save_m2m()
            messages.success(request, 'Teacher added successfully')
            return redirect('admin_teachers')
    else:
        form = TeacherForm()
    
    return render(request, 'admin/add_teacher.html', {'form': form})

@login_required
def admin_students(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    students = Student.objects.all()
    return render(request, 'admin/students.html', {'students': students})

@login_required
def admin_teachers(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    teachers = Teacher.objects.all()
    return render(request, 'admin/teachers.html', {'teachers': teachers})

@login_required
def admin_edit_student(request, student_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        old_semester = student.semester
        old_department = student.department
        
        student.semester = request.POST.get('semester')
        student.phone = request.POST.get('phone')
        student.address = request.POST.get('address')
        student.save()
        
        # Check if semester or department changed to provide enrollment feedback
        if old_semester != student.semester or old_department != student.department:
            from .utils import auto_enroll_student_subjects
            created, updated = auto_enroll_student_subjects(student)
            if created > 0 or updated > 0:
                messages.success(request, f'Student updated successfully. Enrolled in {created} new subjects.')
            else:
                messages.success(request, 'Student updated successfully')
        else:
            messages.success(request, 'Student updated successfully')
        
        return redirect('admin_students')
    
    return render(request, 'admin/edit_student.html', {'student': student})

@login_required
def admin_delete_student(request, student_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    student = get_object_or_404(Student, id=student_id)
    user = student.user
    student.delete()
    user.delete()
    messages.success(request, 'Student deleted successfully')
    return redirect('admin_students')

@login_required
def admin_edit_teacher(request, teacher_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    if request.method == 'POST':
        teacher.phone = request.POST.get('phone')
        teacher.save()
        
        # Update subjects
        subject_ids = request.POST.getlist('subjects')
        teacher.subjects.set(subject_ids)
        
        messages.success(request, 'Teacher updated successfully')
        return redirect('admin_teachers')
    
    departments = Department.objects.all()
    subjects = Subject.objects.all()
    return render(request, 'admin/edit_teacher.html', {
        'teacher': teacher,
        'departments': departments,
        'subjects': subjects
    })

@login_required
def admin_delete_teacher(request, teacher_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    teacher = get_object_or_404(Teacher, id=teacher_id)
    user = teacher.user
    teacher.delete()
    user.delete()
    messages.success(request, 'Teacher deleted successfully')
    return redirect('admin_teachers')

@login_required
def admin_departments(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    departments = Department.objects.all()
    return render(request, 'admin/departments.html', {'departments': departments})

@login_required
def admin_add_department(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department added successfully')
            return redirect('admin_departments')
    else:
        form = DepartmentForm()
    
    return render(request, 'admin/add_department.html', {'form': form})


@login_required
def admin_degrees(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    degrees = Degree.objects.all().order_by('name')
    return render(request, 'admin/degrees.html', {'degrees': degrees})


@login_required
def admin_add_degree(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    if request.method == 'POST':
        form = DegreeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Degree added')
            return redirect('admin_degrees')
    else:
        form = DegreeForm()
    return render(request, 'admin/add_edit_degree.html', {'form': form, 'is_edit': False})


@login_required
def admin_edit_degree(request, degree_id):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    degree = get_object_or_404(Degree, id=degree_id)
    if request.method == 'POST':
        form = DegreeForm(request.POST, instance=degree)
        if form.is_valid():
            form.save()
            messages.success(request, 'Degree updated')
            return redirect('admin_degrees')
    else:
        form = DegreeForm(instance=degree)
    return render(request, 'admin/add_edit_degree.html', {'form': form, 'is_edit': True, 'degree': degree})


@login_required
def admin_delete_degree(request, degree_id):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    degree = get_object_or_404(Degree, id=degree_id)
    if request.method == 'POST':
        degree.delete()
        messages.success(request, 'Degree deleted')
        return redirect('admin_degrees')
    return render(request, 'admin/confirm_delete_degree.html', {'degree': degree})

@login_required
def admin_edit_department(request, department_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    department = get_object_or_404(Department, id=department_id)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully')
            return redirect('admin_departments')
    else:
        form = DepartmentForm(instance=department)
    
    return render(request, 'admin/edit_department.html', {'form': form, 'department': department})

@login_required
def admin_delete_department(request, department_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    department = get_object_or_404(Department, id=department_id)
    department.delete()
    messages.success(request, 'Department deleted successfully')
    return redirect('admin_departments')

@login_required
def admin_subjects(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    subjects = Subject.objects.all().select_related('department')
    return render(request, 'admin/subjects.html', {'subjects': subjects})

@login_required
def admin_add_subject(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject added successfully')
            return redirect('admin_subjects')
    else:
        form = SubjectForm()
    
    return render(request, 'admin/add_subject.html', {'form': form})

@login_required
def admin_edit_subject(request, subject_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject updated successfully')
            return redirect('admin_subjects')
    else:
        form = SubjectForm(instance=subject)
    
    return render(request, 'admin/edit_subject.html', {'form': form, 'subject': subject})

@login_required
def admin_delete_subject(request, subject_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, 'Subject deleted successfully')
    return redirect('admin_subjects')

# ============ Teacher Views ============

@login_required
def teacher_dashboard(request):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    subjects = teacher.subjects.all()
    notices = Notice.objects.filter(created_by=teacher)[:5]
    
    context = {
        'teacher': teacher,
        'subjects': subjects,
        'notices': notices,
    }
    return render(request, 'teacher/dashboard.html', context)

@login_required
def teacher_select_subject_attendance(request):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    subjects = teacher.subjects.all()
    
    return render(request, 'teacher/select_subject_attendance.html', {'subjects': subjects})

@login_required
def teacher_select_subject_marks(request):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    subjects = teacher.subjects.all()
    
    return render(request, 'teacher/select_subject_marks.html', {'subjects': subjects})

@login_required
def teacher_add_student(request):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            student = form.save(commit=False)
            student.user = user
            student.save()
            messages.success(request, 'Student added successfully')
            return redirect('teacher_students')
    else:
        form = StudentForm()
    
    return render(request, 'teacher/add_student.html', {'form': form})

@login_required
def teacher_students(request):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    students = Student.objects.filter(department=teacher.department)
    return render(request, 'teacher/students.html', {'students': students})

@login_required
def teacher_edit_student(request, student_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    student = get_object_or_404(Student, id=student_id, department=teacher.department)

    from .models import Degree

    if request.method == 'POST':
        old_semester = student.semester
        
        # Allow teacher to set semester, phone, address, degree and section
        student.semester = request.POST.get('semester')
        student.phone = request.POST.get('phone')
        student.address = request.POST.get('address')
        degree_id = request.POST.get('degree')
        if degree_id:
            try:
                student.degree = Degree.objects.get(id=degree_id)
            except Degree.DoesNotExist:
                student.degree = None
        else:
            student.degree = None
        student.section = request.POST.get('section')
        student.save()
        
        # Check if semester changed to provide enrollment feedback
        if old_semester != student.semester:
            from .utils import auto_enroll_student_subjects
            created, updated = auto_enroll_student_subjects(student)
            if created > 0:
                messages.success(request, f'Student updated successfully. Enrolled in {created} new subjects.')
            else:
                messages.success(request, 'Student updated successfully')
        else:
            messages.success(request, 'Student updated successfully')
        
        return redirect('teacher_students')

    degrees = Degree.objects.all()
    return render(request, 'teacher/edit_student.html', {'student': student, 'degrees': degrees})


@login_required
def teacher_schedule_exam(request):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    teacher = request.user.teacher

    # Use ExamForm to create exams
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = teacher
            exam.save()
            messages.success(request, 'Exam scheduled successfully')
            return redirect('teacher_dashboard')
    else:
        form = ExamForm()

    exams = Exam.objects.filter(created_by=teacher).order_by('-start_time')
    return render(request, 'teacher/schedule_exam.html', {'form': form, 'exams': exams})


@login_required
def teacher_edit_exam(request, exam_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    teacher = request.user.teacher
    exam = get_object_or_404(Exam, id=exam_id, created_by=teacher)

    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam updated successfully')
            return redirect('teacher_schedule_exam')
    else:
        form = ExamForm(instance=exam)

    exams = Exam.objects.filter(created_by=teacher).order_by('-start_time')
    return render(request, 'teacher/schedule_exam.html', {'form': form, 'exams': exams, 'editing': exam})


@login_required
def teacher_delete_exam(request, exam_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    teacher = request.user.teacher
    exam = get_object_or_404(Exam, id=exam_id, created_by=teacher)

    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted')
        return redirect('teacher_schedule_exam')

    # If GET, show a simple confirmation page
    return render(request, 'teacher/confirm_delete_exam.html', {'exam': exam})


@login_required
def teacher_exam_results(request, exam_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    teacher = request.user.teacher
    exam = get_object_or_404(Exam, id=exam_id, created_by=teacher)

    attempts = ExamAttempt.objects.filter(exam=exam).select_related('student__user')

    # Optionally support CSV download
    if request.GET.get('format') == 'csv':
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{exam.title}_results.csv"'
        writer = csv.writer(response)
        writer.writerow(['Roll Number', 'Student Name', 'Score', 'Submitted At', 'Proctor Log'])
        for a in attempts:
            writer.writerow([a.student.roll_number, a.student.user.get_full_name(), a.score or '', a.submitted_at or '', a.proctor_log or ''])
        return response

    return render(request, 'teacher/exam_results.html', {'exam': exam, 'attempts': attempts})


@login_required
def student_online_exams(request):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')
    student = request.user.student
    now = timezone.now()

    # Active exams (can be taken now)
    active_exams = Exam.objects.filter(start_time__lte=now, end_time__gte=now).order_by('start_time')
    # Upcoming exams
    upcoming_exams = Exam.objects.filter(start_time__gt=now).order_by('start_time')[:10]

    # Attempts by student
    attempts = ExamAttempt.objects.filter(student=student)
    attempt_map = {a.exam_id: a for a in attempts}
    submitted_exam_ids = [a.exam_id for a in attempts if a.is_submitted]

    return render(request, 'student/online_exams.html', {
        'active_exams': active_exams,
        'upcoming_exams': upcoming_exams,
        'attempt_map': attempt_map,
        'submitted_exam_ids': submitted_exam_ids,
    })


@login_required
def student_take_exam(request, exam_id):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')
    student = request.user.student

    exam = get_object_or_404(Exam, id=exam_id)
    now = timezone.now()
    if not (exam.start_time <= now <= exam.end_time):
        messages.error(request, 'This exam is not currently active')
        return redirect('student_online_exams')

    attempt, created = ExamAttempt.objects.get_or_create(exam=exam, student=student)
    if attempt.is_submitted:
        messages.info(request, 'You have already submitted this exam')
        return redirect('student_online_exams')

    questions = exam.questions.all()

    if request.method == 'POST':
        # Gather answers
        answers = {}
        proctor_log = request.POST.get('proctor_log', '')
        total_score = 0.0
        for q in questions:
            key = f'q_{q.id}'
            val = request.POST.get(key)
            answers[str(q.id)] = val
            if q.question_type == 'mcq' and q.correct_answer is not None and val is not None:
                # simple string compare
                if str(val).strip() == str(q.correct_answer).strip():
                    total_score += float(q.marks or 0)

        attempt.answers = answers
        attempt.proctor_log = proctor_log
        attempt.submitted_at = timezone.now()
        attempt.is_submitted = True
        attempt.score = total_score
        attempt.save()

        messages.success(request, f'Exam submitted — Score: {total_score}')
        return redirect('student_online_exams')

    # Remaining time in seconds
    remaining_seconds = int((exam.end_time - now).total_seconds())
    return render(request, 'student/take_exam.html', {
        'exam': exam,
        'questions': questions,
        'attempt': attempt,
        'remaining_seconds': remaining_seconds,
    })


@login_required
def student_exam_result(request, exam_id):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')
    student = request.user.student

    exam = get_object_or_404(Exam, id=exam_id)
    try:
        attempt = ExamAttempt.objects.get(exam=exam, student=student)
    except ExamAttempt.DoesNotExist:
        messages.error(request, 'You have not attempted this exam.')
        return redirect('student_online_exams')

    if not attempt.is_submitted:
        messages.error(request, 'This exam has not been submitted yet.')
        return redirect('student_online_exams')

    # Build per-question breakdown
    breakdown = []
    total_awarded = 0.0
    for q in exam.questions.all():
        student_answer = None
        awarded = None
        if attempt.answers:
            student_answer = attempt.answers.get(str(q.id))
        if q.question_type == 'mcq':
            if student_answer is not None and q.correct_answer is not None and str(student_answer).strip() == str(q.correct_answer).strip():
                awarded = float(q.marks or 0)
            else:
                awarded = 0.0
        else:
            # short answer: not auto-graded
            awarded = None

        if awarded:
            total_awarded += awarded

        breakdown.append({
            'question': q,
            'student_answer': student_answer,
            'correct_answer': q.correct_answer,
            'awarded': awarded,
        })

    # Use stored score if present, otherwise computed total_awarded
    displayed_score = attempt.score if attempt.score is not None else total_awarded

    return render(request, 'student/exam_result.html', {
        'exam': exam,
        'attempt': attempt,
        'breakdown': breakdown,
        'displayed_score': displayed_score,
    })


@login_required
def teacher_manage_questions(request, exam_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    teacher = request.user.teacher
    exam = get_object_or_404(Exam, id=exam_id, created_by=teacher)
    questions = exam.questions.all().order_by('id')
    return render(request, 'teacher/manage_questions.html', {'exam': exam, 'questions': questions})


@login_required
def teacher_add_question(request, exam_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    teacher = request.user.teacher
    exam = get_object_or_404(Exam, id=exam_id, created_by=teacher)

    if request.method == 'POST':
        form = ExamQuestionForm(request.POST)
        if form.is_valid():
            q = form.save(commit=False)
            q.exam = exam
            q.save()
            messages.success(request, 'Question added')
            return redirect('teacher_manage_questions', exam_id=exam.id)
    else:
        form = ExamQuestionForm()
    return render(request, 'teacher/add_edit_question.html', {'form': form, 'exam': exam, 'is_edit': False})


@login_required
def teacher_edit_question(request, question_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    question = get_object_or_404(ExamQuestion, id=question_id)
    if question.exam.created_by != request.user.teacher:
        messages.error(request, 'Access denied')
        return redirect('teacher_dashboard')

    if request.method == 'POST':
        form = ExamQuestionForm(request.POST, instance=question)
        if form.is_valid():
            q = form.save()
            messages.success(request, 'Question updated')
            return redirect('teacher_manage_questions', exam_id=question.exam.id)
    else:
        initial = {}
        if question.choices:
            initial['choices_text'] = '\n'.join(question.choices)
        form = ExamQuestionForm(instance=question, initial=initial)
    return render(request, 'teacher/add_edit_question.html', {'form': form, 'exam': question.exam, 'is_edit': True})


@login_required
def teacher_delete_question(request, question_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    question = get_object_or_404(ExamQuestion, id=question_id)
    if question.exam.created_by != request.user.teacher:
        messages.error(request, 'Access denied')
        return redirect('teacher_dashboard')
    exam_id = question.exam.id
    question.delete()
    messages.success(request, 'Question deleted')
    return redirect('teacher_manage_questions', exam_id=exam_id)

@login_required
def teacher_delete_student(request, student_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    student = get_object_or_404(Student, id=student_id, department=teacher.department)
    user = student.user
    student.delete()
    user.delete()
    messages.success(request, 'Student deleted successfully')
    return redirect('teacher_students')

@login_required
def teacher_mark_attendance(request, subject_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Verify teacher teaches this subject
    if not teacher.subjects.filter(id=subject_id).exists():
        messages.error(request, 'You are not assigned to teach this subject')
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        date = request.POST.get('date')
        student_ids = request.POST.getlist('present')
        
        # Get all students enrolled in this subject (regardless of teacher assignment)
        enrollments = SubjectEnrollment.objects.filter(subject=subject).select_related('student', 'student__user')
        
        # If no enrollments, get students by department and semester and create enrollments
        if not enrollments.exists():
            students = Student.objects.filter(
                department=subject.department,
                semester=subject.semester
            )
            # Create enrollments with current teacher
            for student in students:
                SubjectEnrollment.objects.get_or_create(
                    student=student,
                    subject=subject,
                    defaults={'teacher': teacher}
                )
            enrollments = SubjectEnrollment.objects.filter(subject=subject).select_related('student', 'student__user')
        else:
            # Update teacher assignment for existing enrollments if needed
            for enrollment in enrollments:
                if enrollment.teacher != teacher:
                    enrollment.teacher = teacher
                    enrollment.save()
        
        # Mark attendance for all enrolled students
        for enrollment in enrollments:
            Attendance.objects.update_or_create(
                student=enrollment.student,
                subject=subject,
                date=date,
                defaults={
                    'is_present': str(enrollment.student.id) in student_ids,
                    'marked_by': teacher
                }
            )
        messages.success(request, f'Attendance marked successfully for {enrollments.count()} students')
        return redirect('teacher_view_attendance', subject_id=subject_id)
    
    # Get all enrollments for this subject (not filtered by teacher)
    enrollments = SubjectEnrollment.objects.filter(subject=subject).select_related('student', 'student__user')
    
    # If no enrollments exist, auto-create them for students in same department and semester
    if not enrollments.exists():
        students = Student.objects.filter(
            department=subject.department,
            semester=subject.semester
        )
        
        # Create enrollments with current teacher
        for student in students:
            SubjectEnrollment.objects.get_or_create(
                student=student,
                subject=subject,
                defaults={'teacher': teacher}
            )
        
        # Re-query to get the newly created enrollments
        enrollments = SubjectEnrollment.objects.filter(subject=subject).select_related('student', 'student__user')
    else:
        # Update teacher assignment for existing enrollments
        for enrollment in enrollments:
            if enrollment.teacher != teacher:
                enrollment.teacher = teacher
                enrollment.save()
    
    return render(request, 'teacher/mark_attendance.html', {
        'subject': subject,
        'enrollments': enrollments,
        'today': datetime.now().date()
    })

@login_required
def teacher_view_attendance(request, subject_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Get all students enrolled in this subject
    enrollments = SubjectEnrollment.objects.filter(subject=subject, teacher=teacher)
    
    # Get attendance data for each student
    attendance_data = []
    for enrollment in enrollments:
        total = Attendance.objects.filter(student=enrollment.student, subject=subject).count()
        present = Attendance.objects.filter(student=enrollment.student, subject=subject, is_present=True).count()
        absent = total - present
        percentage = round((present / total * 100), 2) if total > 0 else 0
        
        attendance_data.append({
            'student': enrollment.student,
            'total': total,
            'present': present,
            'absent': absent,
            'percentage': percentage
        })
    
    return render(request, 'teacher/view_attendance.html', {
        'subject': subject,
        'attendance_data': attendance_data
    })

@login_required
def teacher_student_attendance(request, student_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    student = get_object_or_404(Student, id=student_id)
    teacher = request.user.teacher
    
    # Get all subjects this teacher teaches to this student
    enrollments = SubjectEnrollment.objects.filter(
        student=student, 
        teacher=teacher
    )
    
    attendance_records = []
    for enrollment in enrollments:
        records = Attendance.objects.filter(
            student=student,
            subject=enrollment.subject
        ).order_by('-date')[:10]  # Last 10 records
        
        total = Attendance.objects.filter(student=student, subject=enrollment.subject).count()
        present = Attendance.objects.filter(student=student, subject=enrollment.subject, is_present=True).count()
        percentage = round((present / total * 100), 2) if total > 0 else 0
        
        attendance_records.append({
            'subject': enrollment.subject,
            'records': records,
            'total': total,
            'present': present,
            'percentage': percentage
        })
    
    return render(request, 'teacher/student_attendance.html', {
        'student': student,
        'attendance_records': attendance_records
    })


@login_required
def teacher_add_marks(request, subject_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    subject = get_object_or_404(Subject, id=subject_id)
    enrollments = SubjectEnrollment.objects.filter(subject=subject, teacher=teacher)
    
    # If no enrollments exist, auto-create them for students in the same department and semester
    if not enrollments.exists():
        students = Student.objects.filter(
            department=subject.department,
            semester=subject.semester
        )
        for student in students:
            SubjectEnrollment.objects.get_or_create(
                student=student,
                subject=subject,
                defaults={'teacher': teacher}
            )
        enrollments = SubjectEnrollment.objects.filter(subject=subject, teacher=teacher)
    
    if request.method == 'POST':
        for enrollment in enrollments:
            if subject.is_lab:
                practical = request.POST.get(f'practical_{enrollment.id}')
                if practical:
                    enrollment.practical_marks = float(practical)
            else:
                mid1 = request.POST.get(f'mid1_{enrollment.id}')
                mid2 = request.POST.get(f'mid2_{enrollment.id}')
                put = request.POST.get(f'put_{enrollment.id}')
                
                if mid1:
                    enrollment.mid1_marks = float(mid1)
                if mid2:
                    enrollment.mid2_marks = float(mid2)
                if put:
                    enrollment.put_marks = float(put)
            
            enrollment.save()
        
        messages.success(request, 'Marks updated successfully')
        return redirect('teacher_dashboard')
    
    return render(request, 'teacher/add_marks.html', {
        'subject': subject,
        'enrollments': enrollments
    })

@login_required
def teacher_download_scorecard(request, student_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    student = get_object_or_404(Student, id=student_id)
    enrollments = SubjectEnrollment.objects.filter(student=student, subject__semester=student.semester)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="scorecard_{student.roll_number}.csv"'
    
    import csv
    writer = csv.writer(response)
    writer.writerow(['Subject Code', 'Subject Name', 'Mid1', 'Mid2', 'PUT', 'Practical', 'External', 'Total'])
    
    for enrollment in enrollments:
        writer.writerow([
            enrollment.subject.code,
            enrollment.subject.name,
            enrollment.mid1_marks or '-',
            enrollment.mid2_marks or '-',
            enrollment.put_marks or '-',
            enrollment.practical_marks or '-',
            enrollment.external_marks or '-',
            enrollment.total_marks or '-'
        ])
    
    return response


@login_required(login_url='login')
@staff_member_required
def admin_import_fees(request):
    """Allow admin to upload a CSV to bulk allocate fees.

    Expected CSV columns (header): roll_number,title,amount,fine,rewards
    """
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, 'No file uploaded')
            return redirect('admin_fees_list')

        import io, csv
        try:
            decoded = csv_file.read().decode('utf-8')
        except Exception:
            messages.error(request, 'Unable to read uploaded file (ensure UTF-8)')
            return redirect('admin_fees_list')

        reader = csv.DictReader(io.StringIO(decoded))
        created = 0
        updated = 0
        errors = []
        for i, row in enumerate(reader, start=2):
            roll = row.get('roll_number') or row.get('roll')
            title = row.get('title')
            amount = row.get('amount')
            fine = row.get('fine') or 0
            rewards = row.get('rewards') or 0

            if not roll or not title or not amount:
                errors.append(f'Row {i}: missing required fields')
                continue

            try:
                student = Student.objects.get(roll_number=roll)
            except Student.DoesNotExist:
                errors.append(f'Row {i}: student with roll {roll} not found')
                continue

            try:
                amount_val = float(amount)
                fine_val = float(fine)
                rewards_val = float(rewards)
            except Exception:
                errors.append(f'Row {i}: invalid numeric values')
                continue

            fee_obj, created_flag = Fees.objects.update_or_create(
                student=student,
                title=title,
                defaults={
                    'amount': amount_val,
                    'fine': fine_val,
                    'rewards': rewards_val,
                    'allocated_by': request.user,
                }
            )
            if created_flag:
                created += 1
            else:
                updated += 1

        # record import log
        try:
            from .models import ImportLog
            log = ImportLog.objects.create(
                uploaded_by=request.user,
                filename=getattr(csv_file, 'name', ''),
                created_count=created,
                updated_count=updated,
                error_count=len(errors),
                errors_preview='\n'.join(errors[:30])[:1000]
            )
        except Exception:
            log = None

        if created:
            messages.success(request, f'Created {created} fee records')
        if updated:
            messages.success(request, f'Updated {updated} fee records')
        if errors:
            for e in errors[:10]:
                messages.error(request, e)
            if len(errors) > 10:
                messages.error(request, f'and {len(errors)-10} more errors...')

        return redirect('admin_fees_list')

    return render(request, 'admin/import_fees.html')


@login_required(login_url='login')
@staff_member_required
def admin_download_fees_template(request):
    """Return a simple CSV template for admins to download and populate."""
    from django.http import HttpResponse
    import csv

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=fees_template.csv'
    writer = csv.writer(response)
    writer.writerow(['roll_number', 'title', 'amount', 'fine', 'rewards'])
    # provide one example row
    writer.writerow(['2021001', 'tuition', '50000', '0', '0'])
    return response

@login_required
def teacher_download_attendance(request, student_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    student = get_object_or_404(Student, id=student_id)
    attendance_records = Attendance.objects.filter(student=student)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{student.roll_number}.csv"'
    
    import csv
    writer = csv.writer(response)
    writer.writerow(['Date', 'Subject', 'Status', 'Percentage'])
    
    subjects = Subject.objects.filter(semester=student.semester, department=student.department)
    for subject in subjects:
        percentage = get_attendance_percentage(student, subject)
        writer.writerow(['-', subject.name, '-', f'{percentage}%'])
    
    return response

@login_required
def teacher_add_notice(request):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = request.user.teacher
            notice.save()
            messages.success(request, 'Notice posted successfully')
            return redirect('teacher_dashboard')
    else:
        form = NoticeForm()
    
    return render(request, 'teacher/add_notice.html', {'form': form})

# ============ Student Views ============

@login_required
def student_dashboard(request):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')
    
    student = request.user.student
    enrollments = SubjectEnrollment.objects.filter(student=student, subject__semester=student.semester)
    attendance_percentage = get_attendance_percentage(student)
    sgpa = student.calculate_sgpa()
    cgpa = student.calculate_cgpa()
    
    notices = Notice.objects.filter(
        department=student.department,
        semester=student.semester
    ) | Notice.objects.filter(department=None, semester=None)
    notices = notices.distinct()[:10]
    # Load timetable for student's degree+section (if any)
    timetable = None
    try:
        if student.degree and student.section:
            timetable = Timetable.objects.filter(degree=student.degree, section=student.section).first()
    except:
        timetable = None

    context = {
        'student': student,
        'enrollments': enrollments,
        'attendance_percentage': attendance_percentage,
        'sgpa': sgpa,
        'cgpa': cgpa,
        'notices': notices,
        'timetable': timetable,
    }
    return render(request, 'student/dashboard.html', context)


@login_required
def student_timetable(request):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    student = request.user.student
    timetable = None
    if student.degree and student.section and student.semester:
        # match timetable section case-insensitively and filter by semester
        qs = Timetable.objects.filter(
            degree=student.degree,
            section__iexact=student.section,
            semester=student.semester
        ).order_by('-updated_at')
        timetable = None
        if qs.exists():
            # prefer a timetable that has slots saved
            for t in qs:
                if t.slots.exists():
                    timetable = t
                    break
            # fallback to most recently updated
            if timetable is None:
                timetable = qs.first()

    # Build weekly view data. Use timetable.active_days if set.
    default_days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
    if timetable:
        days = timetable.get_active_days_list() or default_days
    else:
        days = default_days
    lectures = list(range(1, 8))
    # nested map: day -> lecture_number -> subject
    slots_map = {d: {l: None for l in lectures} for d in days}
    if timetable:
        for s in timetable.slots.all():
            if s.day in slots_map and s.lecture_number in slots_map[s.day]:
                slots_map[s.day][s.lecture_number] = s.subject
    # Build table rows for template: list of {'day': d, 'cells': [subject_or_None,..]}
    table_rows = []
    for d in days:
        cells = [slots_map[d][l] for l in lectures]
        table_rows.append({'day': d, 'cells': cells})
    return render(request, 'student/timetable.html', {
        'student': student,
        'timetable': timetable,
        'days': days,
        'lectures': lectures,
        'slots_map': slots_map,
        'table_rows': table_rows,
    })


@login_required
def teacher_allocate_weekly_timetable(request):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')

    teacher = request.user.teacher

    # Allow teacher to choose degree, section, and semester to edit
    degrees = Degree.objects.all()
    semesters = list(range(1, 9))  # Semesters 1-8

    selected_degree_id = request.GET.get('degree') or request.POST.get('degree')
    selected_section = request.GET.get('section') or request.POST.get('section')
    selected_semester = request.GET.get('semester') or request.POST.get('semester')
    if selected_section:
        selected_section = selected_section.strip().upper()
    
    # Filter subjects based on teacher's department and selected semester
    subjects = Subject.objects.all()
    if selected_semester and teacher.department:
        try:
            subjects = Subject.objects.filter(
                department=teacher.department,
                semester=int(selected_semester)
            )
        except ValueError:
            subjects = Subject.objects.none()
    elif teacher.department:
        # If no semester selected, show all subjects from teacher's department
        subjects = Subject.objects.filter(department=teacher.department)
    
    timetable = None
    if selected_degree_id and selected_section and selected_semester:
        try:
            deg = Degree.objects.get(id=selected_degree_id)
            timetable, _ = Timetable.objects.get_or_create(
                degree=deg,
                section=selected_section,
                semester=int(selected_semester)
            )
        except (Degree.DoesNotExist, ValueError):
            timetable = None

    # Days and lectures
    all_days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
    lectures = list(range(1, 8))

    # Determine currently selected days for this timetable (for display)
    if timetable:
        selected_days = timetable.get_active_days_list() or all_days
    else:
        selected_days = all_days

    if request.method == 'POST' and timetable:
        # Save selected days from checkboxes
        posted_days = request.POST.getlist('days')
        # Normalize to known day codes, default to none if empty
        posted_days = [d for d in posted_days if d in all_days]
        if not posted_days:
            posted_days = []

        # Persist lecture times (time_1..time_7) and lunch if provided
        for i in range(1, 8):
            tstr = request.POST.get(f'time_{i}')
            if tstr:
                try:
                    parsed = datetime.strptime(tstr, '%H:%M').time()
                except Exception:
                    parsed = None
            else:
                parsed = None
            setattr(timetable, f'lecture{i}', parsed)
        lunch_str = request.POST.get('lunch')
        if lunch_str:
            try:
                timetable.lunch = datetime.strptime(lunch_str, '%H:%M').time()
            except Exception:
                timetable.lunch = None
        else:
            timetable.lunch = None

        # Persist selected days on timetable
        timetable.active_days = ','.join(posted_days)
        timetable.save()

        # Save submitted slots for posted days; remove slots for unselected days
        for d in all_days:
            if d not in posted_days:
                # delete any existing slots for this day
                TimetableSlot.objects.filter(timetable=timetable, day=d).delete()
            else:
                for l in lectures:
                    key = f'slot_{d}_{l}'
                    sub_id = request.POST.get(key)
                    if sub_id:
                        try:
                            sub = Subject.objects.get(id=sub_id)
                        except Subject.DoesNotExist:
                            sub = None
                    else:
                        sub = None
                    TimetableSlot.objects.update_or_create(
                        timetable=timetable,
                        day=d,
                        lecture_number=l,
                        defaults={'subject': sub}
                    )

        messages.success(request, 'Weekly timetable updated')
        # Redirect back to the same page with degree/section/semester selected so teacher sees saved timetable
        if selected_degree_id and selected_section and selected_semester:
            return redirect(f'{request.path}?degree={selected_degree_id}&section={selected_section}&semester={selected_semester}')
        return redirect('teacher_allocate_weekly_timetable')

    # Build existing slots map for the selected days
    # nested map for teacher form convenience: day -> lecture_number -> subject
    slots_map = {d: {l: None for l in lectures} for d in selected_days}
    if timetable:
        for s in timetable.slots.all():
            if s.day in slots_map and s.lecture_number in slots_map[s.day]:
                slots_map[s.day][s.lecture_number] = s.subject
    # Build table rows for template: list of {'day': d, 'cells': [subject_or_None,..]}
    table_rows = []
    for d in selected_days:
        cells = [slots_map[d][l] for l in lectures]
        table_rows.append({'day': d, 'cells': cells})
    return render(request, 'teacher/allocate_weekly_timetable.html', {
        'degrees': degrees,
        'semesters': semesters,
        'subjects': subjects,
        'timetable': timetable,
        'selected_degree_id': int(selected_degree_id) if selected_degree_id else None,
        'selected_section': selected_section,
        'selected_semester': int(selected_semester) if selected_semester else None,
        'days': all_days,
        'selected_days': selected_days,
        'lectures': lectures,
        'slots_map': slots_map,
        'table_rows': table_rows,
    })


@login_required
def teacher_allocate_timetable(request):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')

    teacher = request.user.teacher

    if request.method == 'POST':
        form = TimetableForm(request.POST)
        if form.is_valid():
            degree = form.cleaned_data.get('degree')
            section = form.cleaned_data.get('section')
            if section:
                section = section.strip().upper()
            # Update or create
            obj, created = Timetable.objects.update_or_create(
                degree=degree,
                section=section,
                defaults={
                    'lecture1': form.cleaned_data.get('lecture1'),
                    'lecture1_subject': form.cleaned_data.get('lecture1_subject'),
                    'lecture2': form.cleaned_data.get('lecture2'),
                    'lecture2_subject': form.cleaned_data.get('lecture2_subject'),
                    'lecture3': form.cleaned_data.get('lecture3'),
                    'lecture3_subject': form.cleaned_data.get('lecture3_subject'),
                    'lecture4': form.cleaned_data.get('lecture4'),
                    'lecture4_subject': form.cleaned_data.get('lecture4_subject'),
                    'lecture5': form.cleaned_data.get('lecture5'),
                    'lecture5_subject': form.cleaned_data.get('lecture5_subject'),
                    'lecture6': form.cleaned_data.get('lecture6'),
                    'lecture6_subject': form.cleaned_data.get('lecture6_subject'),
                    'lecture7': form.cleaned_data.get('lecture7'),
                    'lecture7_subject': form.cleaned_data.get('lecture7_subject'),
                    'lunch': form.cleaned_data.get('lunch'),
                }
            )
            messages.success(request, 'Timetable saved')
            return redirect('teacher_dashboard')
    else:
        form = TimetableForm()

    return render(request, 'teacher/allocate_timetable.html', {'form': form})

@login_required
def student_edit_external_marks(request, enrollment_id):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')
    
    enrollment = get_object_or_404(SubjectEnrollment, id=enrollment_id, student=request.user.student)
    
    if request.method == 'POST':
        form = ExternalMarksForm(request.POST, instance=enrollment)
        if form.is_valid():
            form.save()
            messages.success(request, 'External marks updated successfully')
            return redirect('student_dashboard')
    else:
        form = ExternalMarksForm(instance=enrollment)
    
    return render(request, 'student/edit_external_marks.html', {'form': form, 'enrollment': enrollment})

@login_required
def student_attendance_details(request):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')
    
    student = request.user.student
    subjects = Subject.objects.filter(semester=student.semester, department=student.department)
    
    attendance_data = []
    for subject in subjects:
        total = Attendance.objects.filter(student=student, subject=subject).count()
        present = Attendance.objects.filter(student=student, subject=subject, is_present=True).count()
        percentage = round((present / total * 100), 2) if total > 0 else 0
        
        attendance_data.append({
            'subject': subject,
            'total': total,
            'present': present,
            'absent': total - present,
            'percentage': percentage
        })
    
    return render(request, 'student/attendance_details.html', {'attendance_data': attendance_data})

@login_required
def student_placement_cell(request):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')
    
    student = request.user.student
    resume, created = Resume.objects.get_or_create(student=student)
    semester_perfs = SemesterPerformance.objects.filter(student=student).order_by('semester')


    # Always initialize forms for context
    form = ResumeForm(instance=resume)
    sgpa_form = SemesterPerformanceForm()

    # compute CGPA from SemesterPerformance entries (simple average of SGPA values)
    cgpa = None
    if semester_perfs.exists():
        total = 0.0
        count = 0
        for sp in semester_perfs:
            try:
                total += float(sp.sgpa)
                count += 1
            except Exception:
                continue
        cgpa = round(total / count, 2) if count > 0 else None

    # Handle separate form submissions: resume upload or SGPA submission
    if request.method == 'POST':
        # Resume upload form
        if 'resume_submit' in request.POST:
            form = ResumeForm(request.POST, request.FILES, instance=resume)
            if form.is_valid():
                resume_obj = form.save(commit=False)
                resume_obj.student = student

                # Read optional job description provided by student
                job_description = request.POST.get('job_description') or None
                resume_obj.job_description = job_description

                # Calculate ATS score using uploaded resume file if provided, otherwise use existing file
                uploaded_file = request.FILES.get('resume_file')
                ats_score = None
                if uploaded_file:
                    try:
                        ats_score = calculate_ats_score(uploaded_file, job_description=job_description)
                        resume_obj.ats_score = ats_score
                    except Exception:
                        resume_obj.ats_score = None
                else:
                    # if no new upload, try to use existing saved file
                    if resume.resume_file:
                        try:
                            # resume.resume_file is a FileField, open it for reading
                            resume.resume_file.open('rb')
                            with resume.resume_file as existing_file:
                                ats_score = calculate_ats_score(existing_file, job_description=job_description)
                                resume_obj.ats_score = ats_score
                        except Exception:
                            resume_obj.ats_score = resume.ats_score

                # Ensure target resume folder exists under MEDIA_ROOT
                try:
                    resume_dir = os.path.join(settings.MEDIA_ROOT, 'resumes')
                    os.makedirs(resume_dir, exist_ok=True)
                except Exception as e:
                    messages.error(request, f'Unable to prepare media folders: {e}')
                    return redirect('student_placement_cell')

                try:
                    resume_obj.save()
                except Exception as e:
                    import traceback
                    tb = traceback.format_exc()
                    # Log to console for debugging and show user-friendly message
                    print('Error saving resume for student', student.id, e)
                    print(tb)
                    messages.error(request, 'Failed to save uploaded resume. Check server logs or file permissions.')
                    return redirect('student_placement_cell')

                messages.success(request, f'Resume(s) uploaded successfully! ATS Score: {resume_obj.ats_score}')
                return redirect('student_placement_cell')

        # SGPA submission form
        if 'sgpa_submit' in request.POST:
            sgpa_form = SemesterPerformanceForm(request.POST)
            if sgpa_form.is_valid():
                sp = sgpa_form.save(commit=False)
                sp.student = student
                try:
                    sp.save()
                    messages.success(request, f'SGPA for semester {sp.semester} saved successfully')
                except Exception as e:
                    # handle unique constraint update
                    existing = SemesterPerformance.objects.filter(student=student, semester=sp.semester).first()
                    if existing:
                        existing.sgpa = sp.sgpa
                        existing.save()
                        messages.success(request, f'SGPA for semester {existing.semester} updated successfully')
                    else:
                        messages.error(request, 'Unable to save SGPA')
                return redirect('student_placement_cell')

    # Helper: resolve a FileField to a safe URL (or None) by checking storage and searching by basename
    def resolve_file_url(file_field):
        if not file_field:
            return None
        name = getattr(file_field, 'name', None)
        if not name:
            return None
        storage = file_field.storage
        # If storage knows the file exists at its recorded name, return the standard URL
        try:
            if storage.exists(name):
                return file_field.url
        except Exception:
            pass

        # Try locating by basename anywhere under MEDIA_ROOT (fallback)
        base = os.path.basename(name)
        media_root = settings.MEDIA_ROOT
        for root, dirs, files in os.walk(media_root):
            if base in files:
                rel_path = os.path.relpath(os.path.join(root, base), media_root)
                # construct URL using MEDIA_URL
                return settings.MEDIA_URL.rstrip('/') + '/' + rel_path.replace('\\', '/')

        return None

    resume_url = resolve_file_url(resume.resume_file) if resume else None

    context = {
        'form': form,
        'resume': resume,
        'semester_perfs': semester_perfs,
        'cgpa': cgpa,
        'sgpa_form': sgpa_form,
        'resume_url': resume_url,
    }

    return render(request, 'student/placement_cell.html', context)

@login_required
def teacher_view_marks(request, subject_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Get all enrollments for this subject
    enrollments = SubjectEnrollment.objects.filter(
        subject=subject, 
        teacher=teacher
    ).select_related('student', 'student__user')
    
    # Calculate statistics
    marks_data = []
    for enrollment in enrollments:
        internal = enrollment.calculate_internal()
        external = enrollment.external_marks or 0
        # Determine max totals based on subject type
        if enrollment.subject.is_lab:
            max_internal = 40.0
            max_external = 70.0
        else:
            max_internal = 30.0
            max_external = 70.0

        max_total = max_internal + max_external
        total = round((internal or 0) + external, 2)
        percentage = round((total / max_total * 100), 2) if max_total > 0 else 0

        marks_data.append({
            'enrollment': enrollment,
            'internal': internal,
            'external': external,
            'total': total,
            'percentage': percentage,
            'max_total': max_total,
        })
    
    # Sort by roll number
    marks_data.sort(key=lambda x: x['enrollment'].student.roll_number)
    
    return render(request, 'teacher/view_marks.html', {
        'subject': subject,
        'marks_data': marks_data,
        'is_lab': subject.is_lab
    })


# NEW: View individual student marks across all subjects
@login_required
def teacher_student_marks(request, student_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    student = get_object_or_404(Student, id=student_id)
    teacher = request.user.teacher
    
    # Get all enrollments for this student with this teacher
    enrollments = SubjectEnrollment.objects.filter(
        student=student,
        teacher=teacher
    ).select_related('subject')
    
    marks_summary = []
    total_obtained = 0
    total_maximum = 0
    
    for enrollment in enrollments:
        internal = enrollment.calculate_internal()
        external = enrollment.external_marks or 0

        # Determine per-subject maxima
        if enrollment.subject.is_lab:
            max_internal = 40.0
            max_external = 70.0
        else:
            max_internal = 30.0
            max_external = 70.0

        max_marks = max_internal + max_external
        obtained = round((internal or 0) + external, 2)

        total_obtained += obtained
        total_maximum += max_marks

        percentage = round((obtained / max_marks * 100), 2) if max_marks > 0 else 0

        marks_summary.append({
            'subject': enrollment.subject,
            'mid1': enrollment.mid1_marks,
            'mid2': enrollment.mid2_marks,
            'put': enrollment.put_marks,
            'practical': enrollment.practical_marks,
            'internal': internal,
            'external': external,
            'total': obtained,
            'max_marks': max_marks,
            'percentage': percentage,
            'grade': get_grade(obtained, max_marks)
        })
    
    overall_percentage = round((total_obtained / total_maximum * 100), 2) if total_maximum > 0 else 0
    sgpa = student.calculate_sgpa()
    cgpa = student.calculate_cgpa()
    
    return render(request, 'teacher/student_marks.html', {
        'student': student,
        'marks_summary': marks_summary,
        'total_obtained': total_obtained,
        'total_maximum': total_maximum,
        'overall_percentage': overall_percentage,
        'sgpa': sgpa,
        'cgpa': cgpa
    })


# --- Placement exports for teachers -------------------------------------------------
@login_required
def teacher_download_placement_data(request):
    """Export placement/training cell student data as CSV (Excel-friendly).

    Only accessible to users with a `teacher` profile.
    """
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')

    # Query Resume records with related student and user
    resumes = Resume.objects.select_related('student', 'student__user').all()

    # Prepare CSV in memory
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    # Header
    writer.writerow([
        'Roll Number', 'Full Name', 'Email', 'Phone', 'Department', 'Semester',
        '10th %', '12th %', 'ATS Score', 'Resume Filename', 'Resume Path', 'Job Description'
    ])

    for r in resumes:
        student = getattr(r, 'student', None)
        if not student:
            continue

        full_name = student.user.get_full_name() if student.user else ''
        email = student.user.email if student.user else ''
        phone = getattr(student, 'phone', '')
        department = student.department.name if getattr(student, 'department', None) else ''
        semester = getattr(student, 'semester', '')
        tenth = getattr(r, 'tenth_percentage', '')
        twelfth = getattr(r, 'twelfth_percentage', '')
        ats = getattr(r, 'ats_score', '')
        filename = os.path.basename(r.resume_file.name) if r.resume_file else ''
        path = r.resume_file.name if r.resume_file else ''

        writer.writerow([
            smart_str(student.roll_number), smart_str(full_name), smart_str(email), smart_str(phone),
            smart_str(department), smart_str(semester), smart_str(tenth), smart_str(twelfth),
            smart_str(ats), smart_str(filename), smart_str(path), smart_str(getattr(r, 'job_description', '') or '')
        ])

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=placement_data.csv'
    return response


@login_required
def teacher_download_resumes_zip(request):
    """Create a ZIP of all resumes and stream it back to the teacher.

    Skips entries with missing files. Only accessible to users with a `teacher` profile.
    """
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')

    resumes = Resume.objects.exclude(resume_file='').select_related('student', 'student__user')

    # Create in-memory zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for r in resumes:
            if not r.resume_file:
                continue
            file_path = os.path.join(settings.MEDIA_ROOT, r.resume_file.name)
            if not os.path.exists(file_path):
                # try to skip missing files
                continue

            # Use a filename inside zip that is informative: rollname_filename
            student = getattr(r, 'student', None)
            roll = student.roll_number if student else 'unknown'
            arcname = f"{roll}_{os.path.basename(r.resume_file.name)}"
            try:
                zf.write(file_path, arcname)
            except Exception:
                continue

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=all_resumes.zip'
    return response


# NEW: Edit marks for a specific student in a subject
@login_required
def teacher_edit_student_marks(request, enrollment_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    enrollment = get_object_or_404(SubjectEnrollment, id=enrollment_id, teacher=teacher)
    
    if request.method == 'POST':
        subject = enrollment.subject
        
        if subject.is_lab:
            practical = request.POST.get('practical_marks')
            if practical:
                enrollment.practical_marks = float(practical)
        else:
            mid1 = request.POST.get('mid1_marks')
            mid2 = request.POST.get('mid2_marks')
            put = request.POST.get('put_marks')
            
            if mid1:
                enrollment.mid1_marks = float(mid1)
            if mid2:
                enrollment.mid2_marks = float(mid2)
            if put:
                enrollment.put_marks = float(put)
        
        enrollment.save()
        messages.success(request, f'Marks updated successfully for {enrollment.student.user.get_full_name()}')
        return redirect('teacher_view_marks', subject_id=enrollment.subject.id)
    
    return render(request, 'teacher/edit_student_marks.html', {
        'enrollment': enrollment
    })


# Helper function for grade calculation
def get_grade(obtained, maximum):
    if obtained is None or maximum is None or maximum == 0:
        return 'N/A'
    
    percentage = (obtained / maximum) * 100
    
    if percentage >= 90:
        return 'A+'
    elif percentage >= 80:
        return 'A'
    elif percentage >= 70:
        return 'B+'
    elif percentage >= 60:
        return 'B'
    elif percentage >= 50:
        return 'C'
    elif percentage >= 40:
        return 'D'
    else:
        return 'F'


# NEW: Bulk marks entry for a subject
@login_required
def teacher_bulk_marks_entry(request, subject_id):
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        exam_type = request.POST.get('exam_type')  # mid1, mid2, put, or practical
        
        enrollments = SubjectEnrollment.objects.filter(subject=subject, teacher=teacher)
        
        for enrollment in enrollments:
            marks_value = request.POST.get(f'marks_{enrollment.id}')
            if marks_value:
                marks = float(marks_value)
                
                if exam_type == 'mid1':
                    enrollment.mid1_marks = marks
                elif exam_type == 'mid2':
                    enrollment.mid2_marks = marks
                elif exam_type == 'put':
                    enrollment.put_marks = marks
                elif exam_type == 'practical':
                    enrollment.practical_marks = marks
                
                enrollment.save()
        
        messages.success(request, f'Marks updated successfully for {exam_type.upper()}')
        return redirect('teacher_view_marks', subject_id=subject_id)
    
    enrollments = SubjectEnrollment.objects.filter(subject=subject, teacher=teacher)
    
    return render(request, 'teacher/bulk_marks_entry.html', {
        'subject': subject,
        'enrollments': enrollments
    })

# ============ Fees Management Views ============

@login_required(login_url='login')
@staff_member_required
def admin_allocate_fees(request):
    if request.method == 'POST':
        form = FeesForm(request.POST)
        if form.is_valid():
            fees = form.save(commit=False)
            fees.allocated_by = request.user
            fees.save()
            messages.success(request, 'Fees allocated successfully')
            return redirect('admin_fees_list')
    else:
        form = FeesForm()
    
    return render(request, 'admin/allocate_fees.html', {'form': form})

@login_required(login_url='login')
@staff_member_required
def admin_fees_list(request):
    all_fees = Fees.objects.select_related('student__user').all()
    
    # Filter by student if provided
    student_id = request.GET.get('student_id')
    if student_id:
        all_fees = all_fees.filter(student_id=student_id)
    
    # Filter by title if provided
    title = request.GET.get('title')
    if title:
        all_fees = all_fees.filter(title=title)
    
    # Group fees by student
    grouped = {}
    for f in all_fees.order_by('student__roll_number'):
        sid = f.student.id
        if sid not in grouped:
            grouped[sid] = {
                'student': f.student,
                'fees': [],
                'total_amount': 0.0,
                'total_paid': 0.0,
                'total_remaining': 0.0,
            }
        grouped[sid]['fees'].append(f)
        grouped[sid]['total_amount'] += float(f.total_amount or 0)
        grouped[sid]['total_paid'] += float(f.amount_paid or 0)
        grouped[sid]['total_remaining'] += float(f.amount_remaining or 0)

    # Convert to list for template ordering
    grouped_list = [grouped[k] for k in sorted(grouped.keys(), key=lambda x: grouped[x]['student'].roll_number)]

    context = {
        'grouped_fees': grouped_list,
        'title_choices': Fees.TITLE_CHOICES,
    }
    
    return render(request, 'admin/fees_list.html', context)

@login_required(login_url='login')
@staff_member_required
def admin_edit_fees(request, fees_id):
    fees = get_object_or_404(Fees, id=fees_id)
    
    if request.method == 'POST':
        form = FeesForm(request.POST, instance=fees)
        if form.is_valid():
            fees = form.save(commit=False)
            fees.allocated_by = request.user
            fees.save()
            messages.success(request, 'Fees updated successfully')
            return redirect('admin_fees_list')
    else:
        form = FeesForm(instance=fees)
    
    return render(request, 'admin/allocate_fees.html', {'form': form, 'fees': fees})

@login_required(login_url='login')
@staff_member_required
def admin_delete_fees(request, fees_id):
    fees = get_object_or_404(Fees, id=fees_id)
    fees.delete()
    messages.success(request, 'Fees record deleted successfully')
    return redirect('admin_fees_list')

@login_required(login_url='login')
@staff_member_required
def admin_verify_fees(request, fees_id):
    fees = get_object_or_404(Fees, id=fees_id)
    fees.is_verified = True
    fees.verified_by = request.user
    fees.verified_on = datetime.now()
    fees.save()
    messages.success(request, 'Fees verified successfully')
    return redirect('admin_fees_list')

@login_required(login_url='login')
@staff_member_required
def admin_download_fees_report(request):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import inch
    
    # Create the PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="fees_report.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6,
        alignment=1
    )
    elements.append(Paragraph("College Fees Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Get all fees
    all_fees = Fees.objects.all().select_related('student', 'allocated_by')
    
    # Create table data
    data = [['Roll Number', 'Student Name', 'Fee Title', 'Amount', 'Fine', 'Rewards', 'Total', 'Paid', 'Remaining', 'Verified']]
    
    for fee in all_fees:
        data.append([
            fee.student.roll_number,
            fee.student.user.get_full_name(),
            fee.get_title_display(),
            f"₹{fee.amount}",
            f"₹{fee.fine}",
            f"₹{fee.rewards}",
            f"₹{fee.total_amount}",
            f"₹{fee.amount_paid}",
            f"₹{fee.amount_remaining}",
            "Yes" if fee.is_verified else "No"
        ])
    
    # Create table
    table = Table(data, colWidths=[1.2*inch, 1.2*inch, 1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.6*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    return response

@login_required(login_url='login')
@login_required(login_url='login')
def student_fees_dashboard(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found')
        return redirect('dashboard')
    
    student_fees_qs = Fees.objects.filter(student=student).prefetch_related('payments')

    fees_list = []
    total_amount_due = 0
    total_paid = 0
    total_remaining = 0

    for f in student_fees_qs:
        total_amount_due += float(f.total_amount or 0)
        total_paid += float(f.amount_paid or 0)
        total_remaining += float(f.amount_remaining or 0)
        # compute percentage safely
        try:
            percent = int(round((float(f.amount_paid) / float(f.total_amount)) * 100)) if float(f.total_amount) > 0 else 0
        except Exception:
            percent = 0
        fees_list.append({'fee': f, 'percent_paid': max(0, min(percent, 100))})

    context = {
        'student': student,
        'fees_list': fees_list,
        'total_amount_due': total_amount_due,
        'total_paid': total_paid,
        'total_remaining': total_remaining,
    }
    
    return render(request, 'student/fees_dashboard.html', context)

@login_required(login_url='login')
def student_pay_fees(request, fees_id):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found')
        return redirect('student_fees_dashboard')
    
    fees = get_object_or_404(Fees, id=fees_id, student=student)
    
    if request.method == 'POST':
        form = FeePaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            # ensure payment is linked to the correct fee and student
            payment.fee = fees
            # validate amount not exceeding remaining (allow equal or less)
            try:
                amt = float(payment.amount)
            except Exception:
                messages.error(request, 'Invalid amount')
                return render(request, 'student/pay_fees.html', {'fees': fees, 'form': form})

            if amt <= 0:
                messages.error(request, 'Payment amount must be positive')
                return render(request, 'student/pay_fees.html', {'fees': fees, 'form': form})

            if amt > float(fees.amount_remaining):
                messages.error(request, 'Payment exceeds remaining due amount')
                return render(request, 'student/pay_fees.html', {'fees': fees, 'form': form})

            # Store payment details in session for confirmation
            request.session['pending_payment'] = {
                'fees_id': fees.id,
                'amount': str(amt),
                'payment_method': payment.payment_method,
                'remarks': payment.remarks,
                'transaction_id': payment.transaction_id or '',
            }
            # Redirect to confirmation page
            return redirect('student_confirm_payment')
    else:
        form = FeePaymentForm()
    
    context = {
        'fees': fees,
        'form': form,
    }
    
    return render(request, 'student/pay_fees.html', context)

@login_required(login_url='login')
def student_confirm_payment(request):
    """Confirm payment by re-authenticating with username and password."""
    pending_payment = request.session.get('pending_payment')
    if not pending_payment:
        messages.error(request, 'No pending payment found')
        return redirect('student_fees_dashboard')
    
    try:
        student = Student.objects.get(user=request.user)
        fees = get_object_or_404(Fees, id=pending_payment['fees_id'], student=student)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found')
        return redirect('student_fees_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Verify credentials
        user = authenticate(request, username=username, password=password)
        if user and user == request.user:
            # Credentials correct, save payment
            from uuid import uuid4
            payment = FeePayment(
                fee=fees,
                amount=float(pending_payment['amount']),
                payment_method=pending_payment['payment_method'],
                remarks=pending_payment['remarks'],
                transaction_id=pending_payment['transaction_id'] or str(uuid4())
            )
            payment.save()
            
            # Clear session
            del request.session['pending_payment']
            
            messages.success(request, f'Payment of ₹{payment.amount} confirmed and recorded successfully')
            return redirect('student_fees_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    context = {
        'fees': fees,
        'amount': pending_payment['amount'],
    }
    
    return render(request, 'student/confirm_payment.html', context)

@login_required(login_url='login')
def student_download_no_dues(request):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    from datetime import datetime
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found')
        return redirect('student_fees_dashboard')
    
    # Check if student has any outstanding fees
    student_fees = Fees.objects.filter(student=student)
    has_outstanding = any(f.amount_remaining > 0 for f in student_fees)
    
    # Create the PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="no_dues_{student.roll_number}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6,
        alignment=1
    )
    elements.append(Paragraph("No Dues Certificate", title_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Student Details
    student_details = f"""
    <b>Roll Number:</b> {student.roll_number}<br/>
    <b>Name:</b> {student.user.get_full_name()}<br/>
    <b>Department:</b> {student.department.name}<br/>
    <b>Semester:</b> {student.semester}<br/>
    <b>Date:</b> {datetime.now().strftime('%d-%m-%Y')}<br/>
    """
    elements.append(Paragraph(student_details, styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Fees Summary
    if has_outstanding:
        elements.append(Paragraph("<b style='color:red;'>Status: Has Outstanding Fees</b>", styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Create fees table
        data = [['Fee Title', 'Total Amount', 'Amount Paid', 'Amount Due']]
        for fee in student_fees:
            if fee.amount_remaining > 0:
                data.append([
                    fee.get_title_display(),
                    f"₹{fee.total_amount}",
                    f"₹{fee.amount_paid}",
                    f"₹{fee.amount_remaining}"
                ])
        
        table = Table(data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef4444')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("<b style='color:green;'>Status: No Outstanding Dues</b>", styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("This certificate certifies that the student has paid all outstanding fees.", styles['Normal']))
    
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("_" * 50, styles['Normal']))
    elements.append(Paragraph("Administrator Signature", styles['Normal']))
    
    doc.build(elements)
    
    return response

@login_required(login_url='login')
def student_fee_details(request, fees_id):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found')
        return redirect('student_fees_dashboard')
    
    fees = get_object_or_404(Fees, id=fees_id, student=student)
    payments = FeePayment.objects.filter(fee=fees).order_by('-paid_on')
    
    context = {
        'fees': fees,
        'payments': payments,
    }
    
    return render(request, 'student/fee_details.html', context)


# ============ Study Materials (Notes) Views ============

@login_required
def teacher_study_materials(request):
    """Teacher view to manage study materials"""
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    materials = StudyMaterial.objects.filter(uploaded_by=teacher).order_by('-uploaded_at')
    
    context = {
        'materials': materials,
    }
    return render(request, 'teacher/study_materials.html', context)


@login_required
def teacher_upload_material(request):
    """Teacher upload new study material"""
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    
    if request.method == 'POST':
        form = StudyMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.uploaded_by = teacher
            material.save()
            messages.success(request, 'Study material uploaded successfully!')
            return redirect('teacher_study_materials')
    else:
        form = StudyMaterialForm()
        # Filter subjects to only those taught by this teacher
        form.fields['subject'].queryset = teacher.subjects.all()
    
    context = {
        'form': form,
    }
    return render(request, 'teacher/upload_material.html', context)


@login_required
def teacher_edit_material(request, material_id):
    """Teacher edit study material"""
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    material = get_object_or_404(StudyMaterial, id=material_id, uploaded_by=teacher)
    
    if request.method == 'POST':
        form = StudyMaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, 'Study material updated successfully!')
            return redirect('teacher_study_materials')
    else:
        form = StudyMaterialForm(instance=material)
        form.fields['subject'].queryset = teacher.subjects.all()
    
    context = {
        'form': form,
        'material': material,
    }
    return render(request, 'teacher/edit_material.html', context)


@login_required
def teacher_delete_material(request, material_id):
    """Teacher delete study material"""
    if not hasattr(request.user, 'teacher'):
        return redirect('dashboard')
    
    teacher = request.user.teacher
    material = get_object_or_404(StudyMaterial, id=material_id, uploaded_by=teacher)
    
    if request.method == 'POST':
        material.delete()
        messages.success(request, 'Study material deleted successfully!')
        return redirect('teacher_study_materials')
    
    context = {
        'material': material,
    }
    return render(request, 'teacher/confirm_delete_material.html', context)


@login_required
def student_study_materials(request):
    """Student view to see and download study materials"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found')
        return redirect('dashboard')
    
    # Get student's subjects based on department and semester
    subjects = Subject.objects.filter(
        department=student.department,
        semester=student.semester
    )
    
    # Get materials for these subjects (filter by section or materials for all sections)
    materials = StudyMaterial.objects.filter(
        subject__in=subjects
    ).filter(
        Q(section='') | Q(section=student.section)
    ).select_related('subject', 'uploaded_by').order_by('subject', '-uploaded_at')
    
    # Group materials by subject
    materials_by_subject = {}
    for material in materials:
        subject_name = material.subject.name
        if subject_name not in materials_by_subject:
            materials_by_subject[subject_name] = []
        materials_by_subject[subject_name].append(material)
    
    context = {
        'materials_by_subject': materials_by_subject,
        'student': student,
    }
    return render(request, 'student/study_materials.html', context)

