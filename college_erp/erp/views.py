from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Avg, Count
from datetime import datetime, timedelta
from .models import *
from .forms import *
from .utils import *

from django.contrib.admin.views.decorators import staff_member_required

# ============ Authentication Views ============

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


def logout_view(request):
    logout(request)
    return redirect('login')

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
        student.semester = request.POST.get('semester')
        student.phone = request.POST.get('phone')
        student.address = request.POST.get('address')
        student.save()
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
    
    if request.method == 'POST':
        student.semester = request.POST.get('semester')
        student.phone = request.POST.get('phone')
        student.address = request.POST.get('address')
        student.save()
        messages.success(request, 'Student updated successfully')
        return redirect('teacher_students')
    
    return render(request, 'teacher/edit_student.html', {'student': student})

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
    
    if request.method == 'POST':
        date = request.POST.get('date')
        student_ids = request.POST.getlist('present')
        
        # Get all students enrolled in this subject with this teacher
        enrollments = SubjectEnrollment.objects.filter(subject=subject, teacher=teacher)
        
        # If no enrollments, get students by department and semester
        if not enrollments.exists():
            students = Student.objects.filter(
                department=subject.department,
                semester=subject.semester
            )
            # Create enrollments on the fly
            for student in students:
                enrollment, created = SubjectEnrollment.objects.get_or_create(
                    student=student,
                    subject=subject,
                    defaults={'teacher': teacher}
                )
            enrollments = SubjectEnrollment.objects.filter(subject=subject, teacher=teacher)
        
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
        messages.success(request, f'Attendance marked successfully for {len(enrollments)} students')
        return redirect('teacher_view_attendance', subject_id=subject_id)
    
    # Get enrollments or create them if they don't exist
    enrollments = SubjectEnrollment.objects.filter(subject=subject, teacher=teacher)
    
    # If no enrollments exist, get all students from the same department and semester
    if not enrollments.exists():
        students = Student.objects.filter(
            department=subject.department,
            semester=subject.semester
        )
        # Auto-create enrollments
        for student in students:
            SubjectEnrollment.objects.get_or_create(
                student=student,
                subject=subject,
                defaults={'teacher': teacher}
            )
        enrollments = SubjectEnrollment.objects.filter(subject=subject, teacher=teacher)
    
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
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'attendance_percentage': attendance_percentage,
        'sgpa': sgpa,
        'cgpa': cgpa,
        'notices': notices,
    }
    return render(request, 'student/dashboard.html', context)

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
    resume = Resume.objects.filter(student=student).first()
    
    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES, instance=resume)
        if form.is_valid():
            resume_obj = form.save(commit=False)
            resume_obj.student = student
            
            # Calculate ATS score
            resume_file = request.FILES.get('resume_file')
            if resume_file:
                ats_score = calculate_ats_score(resume_file)
                resume_obj.ats_score = ats_score
            
            resume_obj.save()
            messages.success(request, f'Resume uploaded successfully! ATS Score: {resume_obj.ats_score}')
            return redirect('student_placement_cell')
    else:
        form = ResumeForm(instance=resume)
    
    return render(request, 'student/placement_cell.html', {'form': form, 'resume': resume})

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
        marks_data.append({
            'enrollment': enrollment,
            'internal': internal,
            'total': enrollment.total_marks or 0,
            'percentage': round((enrollment.total_marks / 160 * 100), 2) if enrollment.total_marks else 0
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
        max_marks = 160  # 60 internal + 100 external
        obtained = enrollment.total_marks or 0
        
        total_obtained += obtained
        total_maximum += max_marks
        
        marks_summary.append({
            'subject': enrollment.subject,
            'mid1': enrollment.mid1_marks,
            'mid2': enrollment.mid2_marks,
            'put': enrollment.put_marks,
            'practical': enrollment.practical_marks,
            'internal': internal,
            'external': enrollment.external_marks,
            'total': obtained,
            'max_marks': max_marks,
            'percentage': round((obtained / max_marks * 100), 2) if obtained else 0,
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
