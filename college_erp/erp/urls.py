from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.role_selection, name='role_selection'),
    path('login/', views.login_view, name='login'),
    path('student-login/', views.student_login, name='student_login'),
    path('teacher-login/', views.teacher_login, name='teacher_login'),
    path('admin-login/', views.admin_login, name='admin_login'),
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
    path('admin/degrees/', views.admin_degrees, name='admin_degrees'),
    path('admin/degrees/add/', views.admin_add_degree, name='admin_add_degree'),
    path('admin/degrees/<int:degree_id>/edit/', views.admin_edit_degree, name='admin_edit_degree'),
    path('admin/degrees/<int:degree_id>/delete/', views.admin_delete_degree, name='admin_delete_degree'),
    path('admin/subjects/', views.admin_subjects, name='admin_subjects'),
    path('admin/add-subject/', views.admin_add_subject, name='admin_add_subject'),
    path('admin/edit-subject/<int:subject_id>/', views.admin_edit_subject, name='admin_edit_subject'),
    path('admin/delete-subject/<int:subject_id>/', views.admin_delete_subject, name='admin_delete_subject'),
    
    # Teacher
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/schedule-exam/', views.teacher_schedule_exam, name='teacher_schedule_exam'),
    path('teacher/timetable/allocate/', views.teacher_allocate_timetable, name='teacher_allocate_timetable'),
    path('teacher/timetable/weekly/', views.teacher_allocate_weekly_timetable, name='teacher_allocate_weekly_timetable'),
    path('teacher/exam/<int:exam_id>/questions/', views.teacher_manage_questions, name='teacher_manage_questions'),
    path('teacher/exam/<int:exam_id>/questions/add/', views.teacher_add_question, name='teacher_add_question'),
    path('teacher/question/<int:question_id>/edit/', views.teacher_edit_question, name='teacher_edit_question'),
    path('teacher/question/<int:question_id>/delete/', views.teacher_delete_question, name='teacher_delete_question'),
    path('teacher/exam/<int:exam_id>/edit/', views.teacher_edit_exam, name='teacher_edit_exam'),
    path('teacher/exam/<int:exam_id>/delete/', views.teacher_delete_exam, name='teacher_delete_exam'),
    path('teacher/exam/<int:exam_id>/results/', views.teacher_exam_results, name='teacher_exam_results'),
    
        # Admin Fees Management
        path('admin/allocate-fees/', views.admin_allocate_fees, name='admin_allocate_fees'),
        path('admin/fees-list/', views.admin_fees_list, name='admin_fees_list'),
        path('admin/import-fees/', views.admin_import_fees, name='admin_import_fees'),
        path('admin/edit-fees/<int:fees_id>/', views.admin_edit_fees, name='admin_edit_fees'),
        path('admin/download-fees-template/', views.admin_download_fees_template, name='admin_download_fees_template'),
        path('admin/delete-fees/<int:fees_id>/', views.admin_delete_fees, name='admin_delete_fees'),
        path('admin/verify-fees/<int:fees_id>/', views.admin_verify_fees, name='admin_verify_fees'),
        path('admin/download-fees-report/', views.admin_download_fees_report, name='admin_download_fees_report'),
    
        # Student Fees Management
        path('student/fees/', views.student_fees_dashboard, name='student_fees_dashboard'),
    path('student/pay-fees/<int:fees_id>/', views.student_pay_fees, name='student_pay_fees'),
    path('student/confirm-payment/', views.student_confirm_payment, name='student_confirm_payment'),
    path('student/fee-details/<int:fees_id>/', views.student_fee_details, name='student_fee_details'),
    path('student/download-no-dues/', views.student_download_no_dues, name='student_download_no_dues'),    path('teacher/select-subject-attendance/', views.teacher_select_subject_attendance, name='teacher_select_subject_attendance'),
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
    path('teacher/download-placement-data/', views.teacher_download_placement_data, name='teacher_download_placement_data'),
    path('teacher/download-resumes-zip/', views.teacher_download_resumes_zip, name='teacher_download_resumes_zip'),
    
    # Teacher Study Materials
    path('teacher/study-materials/', views.teacher_study_materials, name='teacher_study_materials'),
    path('teacher/study-materials/upload/', views.teacher_upload_material, name='teacher_upload_material'),
    path('teacher/study-materials/<int:material_id>/edit/', views.teacher_edit_material, name='teacher_edit_material'),
    path('teacher/study-materials/<int:material_id>/delete/', views.teacher_delete_material, name='teacher_delete_material'),
    
    
    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/timetable/', views.student_timetable, name='student_timetable'),
    path('student/online-exams/', views.student_online_exams, name='student_online_exams'),
    path('student/take-exam/<int:exam_id>/', views.student_take_exam, name='student_take_exam'),
    path('student/exam/<int:exam_id>/result/', views.student_exam_result, name='student_exam_result'),
    path('student/edit-external-marks/<int:enrollment_id>/', views.student_edit_external_marks, name='student_edit_external_marks'),
    path('student/attendance/', views.student_attendance_details, name='student_attendance_details'),
    path('student/placement/', views.student_placement_cell, name='student_placement_cell'),
    
    # Student Study Materials
    path('student/study-materials/', views.student_study_materials, name='student_study_materials'),
]