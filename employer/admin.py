from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(Employeer)
class EmployeerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'mobile', 'is_partnership', 'is_deleted', 'created')
    search_fields = ('name', 'email', 'mobile')
    list_filter = ('is_partnership', 'is_deleted', 'created')
    ordering = ('-created',)


@admin.register(CountriesSelector)
class CountriesSelectorAdmin(admin.ModelAdmin):
    list_display=('id','country','created_at')


@admin.register(StateMaster)
class StateMasterAdmin(admin.ModelAdmin):
    list_display = ('id','state')


@admin.register(DistrictMaster)
class DistrictMasterAdmin(admin.ModelAdmin):
    list_display=('id','district','created_at')
    

@admin.register(RateEmployee)
class RateEmployeeAdmin(admin.ModelAdmin):
    list_display=('id','employee','rating','created_at')

######################3---------------------------eMPLOYEER bUSINESS DETAILS
@admin.register(EmployerBusinessDetails)
class EmployerBusinessDetailsAdmin(admin.ModelAdmin):
    list_display = ('employer', 'business_location', 'business_type', 'registration_number', 'gst_number', 'is_deleted')
    list_filter = ('business_type', 'is_deleted', 'country', 'state')
    search_fields = ('employer__name', 'business_location', 'registration_number', 'gst_number')
#############----------------------------Employeer COMPANY pOLICES DETAILS
@admin.register(EmployerCompanyPolicies)
class EmployerCompanyPoliciesAdmin(admin.ModelAdmin):
    list_display = ('employer', 'notice_period_days', 'probation_period_days', 'total_annual_leaves', 'working_hours_per_day')
    list_filter = ('notice_period_days', 'probation_period_days', 'total_annual_leaves')
    search_fields = ('employer__name',)

####################----------------------------EmployerS cOMPANY eMAIL DETAILS
@admin.register(EmployerEmailsDetails)
class EmployerEmailsDetailsAdmin(admin.ModelAdmin):
    list_display = ('employer', 'email', 'email_type', 'is_deleted')
    list_filter = ('email_type', 'is_deleted')
    search_fields = ('employer__name', 'email')
###########################-----------------------Employer Type Contract
@admin.register(EmployerrTypeContract)
class EmployerTypeContractAdmin(admin.ModelAdmin):
    list_display = ('employer','is_deleted')
######################-------------EmployerPaymentCycle
@admin.register(EmployerPaymentCycle)
class EmployerPaymentCycleAdmin(admin.ModelAdmin):
    list_display = ('employer','payment_cycle')
    search_fields = ('employer__name',)
    list_filter = ('payment_cycle',)