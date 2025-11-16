from django.contrib import admin
from .models import *

admin.site.register(Department)
admin.site.register(Subject)
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(SubjectEnrollment)
admin.site.register(Attendance)
admin.site.register(Notice)
admin.site.register(Resume)