from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(GigEmployee)
class GigEmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_name","mobile", "is_deleted")
    search_fields = ("employee_name", "employee_id", "mobile")
    list_filter = ("is_deleted",)
    
@admin.register(BankDetails)
class BankDetailsAdmin(admin.ModelAdmin):
    list_display = ('id','bank_name', 'account_number', 'branch_name', 'ifsc_code', 'is_deleted')
    search_fields = ('bank_name', 'account_number', 'ifsc_code')
    list_filter = ('is_deleted',)
    ordering = ('-created_at',)

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
    list_display = ("employee","daily_salary","salary_date")
    search_fields = ("employee__employee_name",)
    list_filter = ("salary_date",)

@admin.register(SalaryDetails)
class SalaryDetailsAdmin(admin.ModelAdmin):
    list_display = ("employee", "earned_wages", "ewa_limit")
    search_fields = ("employee__employee_name",)

@admin.register(EWATransaction)
class EWARequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "amount","interest_amount","interest_rate")
    list_filter = ("status",)