from django.contrib import admin
from django.http import HttpResponse
import csv
from django.utils import timezone
from .models import *


@admin.action(description='Export selected fees as CSV')
def export_fees_as_csv(modeladmin, request, queryset):
	meta = modeladmin.model._meta
	field_names = ['student_roll', 'student_name', 'title', 'amount', 'fine', 'rewards', 'total_amount', 'amount_paid', 'amount_remaining', 'is_verified', 'allocated_on']

	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename=fees_export.csv'
	writer = csv.writer(response)
	writer.writerow(field_names)
	for obj in queryset:
		writer.writerow([
			obj.student.roll_number,
			obj.student.user.get_full_name(),
			obj.get_title_display(),
			str(obj.amount),
			str(obj.fine),
			str(obj.rewards),
			str(obj.total_amount),
			str(obj.amount_paid),
			str(obj.amount_remaining),
			'Yes' if obj.is_verified else 'No',
			obj.allocated_on.strftime('%Y-%m-%d %H:%M') if obj.allocated_on else '',
		])
	return response


@admin.action(description='Verify selected fees')
def verify_selected_fees(modeladmin, request, queryset):
	count = 0
	for obj in queryset:
		if not obj.is_verified:
			obj.is_verified = True
			obj.verified_by = request.user
			obj.verified_on = timezone.now()
			obj.save()
			count += 1
	modeladmin.message_user(request, f'{count} fees verified')


class FeesAdmin(admin.ModelAdmin):
	list_display = ('student', 'title', 'amount', 'fine', 'rewards', 'total_amount', 'amount_paid', 'amount_remaining', 'is_verified', 'allocated_on')
	list_filter = ('title', 'is_verified', 'allocated_on')
	search_fields = ('student__roll_number', 'student__user__first_name', 'student__user__last_name')
	actions = [export_fees_as_csv, verify_selected_fees]


class FeePaymentAdmin(admin.ModelAdmin):
	list_display = ('fee', 'amount', 'payment_method', 'transaction_id', 'paid_on')
	list_filter = ('payment_method', 'paid_on')
	search_fields = ('fee__student__roll_number', 'transaction_id')


admin.site.register(Department)
admin.site.register(Subject)
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(SubjectEnrollment)
admin.site.register(Attendance)
admin.site.register(Notice)
admin.site.register(Resume)
admin.site.register(Fees, FeesAdmin)
admin.site.register(FeePayment, FeePaymentAdmin)
class DegreeAdmin(admin.ModelAdmin):
	list_display = ('name', 'university_name', 'code')
	search_fields = ('name', 'university_name')

admin.site.register(Degree, DegreeAdmin)
from .models import ImportLog


class ImportLogAdmin(admin.ModelAdmin):
	list_display = ('uploaded_at', 'uploaded_by', 'filename', 'created_count', 'updated_count', 'error_count')
	readonly_fields = ('uploaded_at', 'uploaded_by', 'filename', 'created_count', 'updated_count', 'error_count', 'errors_preview')


admin.site.register(ImportLog, ImportLogAdmin)
from .models import Timetable


class TimetableAdmin(admin.ModelAdmin):
	list_display = ('degree', 'section', 'updated_at')
	search_fields = ('degree__name', 'section')


admin.site.register(Timetable, TimetableAdmin)
class TimetableSlotAdmin(admin.ModelAdmin):
	list_display = ('timetable', 'day', 'lecture_number', 'subject')
	list_filter = ('day', 'lecture_number')


admin.site.register(TimetableSlot, TimetableSlotAdmin)


class StudyMaterialAdmin(admin.ModelAdmin):
	list_display = ('title', 'subject', 'section', 'uploaded_by', 'uploaded_at')
	list_filter = ('subject', 'section', 'uploaded_at')
	search_fields = ('title', 'description', 'subject__name', 'subject__code')


admin.site.register(StudyMaterial, StudyMaterialAdmin)
