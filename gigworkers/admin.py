from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(GigEmployee)
class GigEmployeeAdmin(admin.ModelAdmin):
    list_display = ("name","mobile", "is_deleted")
    search_fields = ("name", "employee_id", "mobile")
    list_filter = ("is_deleted")
    
    
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id','mobile','access_token','last_login','user_type','token_expires_at')
    list_filter=('user_type',)

@admin.register(EmployeeVerification)
class EmployeeVerificationAdmin(admin.ModelAdmin):
    list_display = ("employee", "pan_number", "aadhar_number", "is_verified")
    search_fields = ("pan_number", "aadhar_number")
    list_filter = ("is_verified",)

@admin.register(SalaryHistory)
class SalaryHistoryAdmin(admin.ModelAdmin):
    list_display = ("employee", "salary_amount", "start_date", "end_date", "days_paid")
    search_fields = ("employee__name",)
    list_filter = ("start_date", "end_date")

@admin.register(SalaryDetails)
class SalaryDetailsAdmin(admin.ModelAdmin):
    list_display = ("employee", "salary_amount", "employment_status", "last_salary_date", "earned_wages", "ewa_limit")
    search_fields = ("employee__name",)
    list_filter = ("employment_status", "last_updated")

@admin.register(EWARequest)
class EWARequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "amount_requested", "status", "requested_at", "approved_at")
    search_fields = ("employee__name",)
    list_filter = ("status", "requested_at")