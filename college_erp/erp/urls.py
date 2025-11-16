from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Admin (Custom Admin Panel)
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/students/', views.admin_students, name='admin_students'),
    path('admin/teachers/', views.admin_teachers, name='admin_teachers'),
    path('admin/add-student/', views.admin_add_student, name='admin_add_student'),
    path('admin/add-teacher/', views.admin_add_teacher, name='admin_add_teacher'),
    path('admin/edit-student/<int:student_id>/', views.admin_edit_student, name='admin_edit_student'),
    path('admin/delete-student/<int:student_id>/', views.admin_delete_student, name='admin_delete_student'),
    path('admin/edit-teacher/<int:teacher_id>/', views.admin_edit_teacher, name='admin_edit_teacher'),
    path('admin/delete-teacher/<int:teacher_id>/', views.admin_delete_teacher, name='admin_delete_teacher'),
    path('admin/departments/', views.admin_departments, name='admin_departments'),
    path('admin/add-department/', views.admin_add_department, name='admin_add_department'),
    path('admin/edit-department/<int:department_id>/', views.admin_edit_department, name='admin_edit_department'),
    path('admin/delete-department/<int:department_id>/', views.admin_delete_department, name='admin_delete_department'),
    path('admin/subjects/', views.admin_subjects, name='admin_subjects'),
    path('admin/add-subject/', views.admin_add_subject, name='admin_add_subject'),
    path('admin/edit-subject/<int:subject_id>/', views.admin_edit_subject, name='admin_edit_subject'),
    path('admin/delete-subject/<int:subject_id>/', views.admin_delete_subject, name='admin_delete_subject'),
    
    # Teacher
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/select-subject-attendance/', views.teacher_select_subject_attendance, name='teacher_select_subject_attendance'),
    path('teacher/select-subject-marks/', views.teacher_select_subject_marks, name='teacher_select_subject_marks'),
    path('teacher/add-student/', views.teacher_add_student, name='teacher_add_student'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/edit-student/<int:student_id>/', views.teacher_edit_student, name='teacher_edit_student'),
    path('teacher/delete-student/<int:student_id>/', views.teacher_delete_student, name='teacher_delete_student'),
    path('teacher/mark-attendance/<int:subject_id>/', views.teacher_mark_attendance, name='teacher_mark_attendance'),
    path('teacher/add-marks/<int:subject_id>/', views.teacher_add_marks, name='teacher_add_marks'),
    path('teacher/download-scorecard/<int:student_id>/', views.teacher_download_scorecard, name='teacher_download_scorecard'),
    path('teacher/download-attendance/<int:student_id>/', views.teacher_download_attendance, name='teacher_download_attendance'),
    path('teacher/add-notice/', views.teacher_add_notice, name='teacher_add_notice'),
    path('teacher/view-attendance/<int:subject_id>/', views.teacher_view_attendance, name='teacher_view_attendance'),
    path('teacher/student-attendance/<int:student_id>/', views.teacher_student_attendance, name='teacher_student_attendance'),
    path('teacher/view-marks/<int:subject_id>/', views.teacher_view_marks, name='teacher_view_marks'),
    path('teacher/student-marks/<int:student_id>/', views.teacher_student_marks, name='teacher_student_marks'),
    path('teacher/edit-marks/<int:enrollment_id>/', views.teacher_edit_student_marks, name='teacher_edit_student_marks'),
    path('teacher/bulk-marks/<int:subject_id>/', views.teacher_bulk_marks_entry, name='teacher_bulk_marks_entry'),
    
    
    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/edit-external-marks/<int:enrollment_id>/', views.student_edit_external_marks, name='student_edit_external_marks'),
    path('student/attendance/', views.student_attendance_details, name='student_attendance_details'),
    path('student/placement/', views.student_placement_cell, name='student_placement_cell'),
]