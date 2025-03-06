from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(Employeer)
class EmployeerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'mobile', 'is_partnership', 'is_deleted', 'created')
    search_fields = ('name', 'email', 'mobile')
    list_filter = ('is_partnership', 'is_deleted', 'created')
    ordering = ('-created',)

@admin.register(AssociatedEmployees)
class AssociatedEmployeesAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee_name', 'employee_id', 'email', 'phone_number', 'designation', 'is_active')
    search_fields = ('employee_name', 'employee_id', 'email', 'phone_number')
    list_filter = ('is_active', 'is_deleted', 'date_joined')
    ordering = ('-date_joined',)

@admin.register(BankDetails)
class BankDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'associated_employeer', 'bank_name', 'account_number', 'branch_name', 'ifsc_code', 'is_deleted')
    search_fields = ('bank_name', 'account_number', 'ifsc_code')
    list_filter = ('is_deleted',)
    ordering = ('-created_at',)
