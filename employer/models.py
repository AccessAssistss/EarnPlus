from django.db import models
from gigworkers.managers import *
from datetime import timedelta
from django.utils import timezone
#------------------------------EMPLOYERR MODELS
class Employeer(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=100,null=True, blank=True)
    company_profile=models.FileField(upload_to='employee/profile',null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=128)
    fcm_token = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=10, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    is_partnership = models.BooleanField(default=False)

#######--------------------------------Employeer Associated
class AssociatedEmployees(models.Model):
    employeer = models.ForeignKey(Employeer, on_delete=models.CASCADE,null=True,blank=True)
    EMPLOYMENT_TYPE_CHOICES = [
        ('SALARIED', 'Salaried Employee'),
        ('CONTRACTUAL_FIXED', 'Contractual with Fixed Salary'),
        ('CONTRACTUAL_VARIABLE', 'Contractual with Variable Income'),
        ('GIG_WORKER', 'Gig Worker with Variable Income')
    ]
    payment_cycle = models.CharField(max_length=20, choices=[
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('BIWEEKLY', 'Bi-Weekly'),
        ('MONTHLY', 'Monthly')
    ], default='MONTHLY')
    employment_type = models.CharField(max_length=50, choices=EMPLOYMENT_TYPE_CHOICES, default='SALARIED')
    employee_name = models.CharField(max_length=100, null=True, blank=True)
    employee_id = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True) 
    dob = models.DateField(null=True, blank=True) 
    department = models.CharField(max_length=100, null=True, blank=True)
    date_joined = models.DateField(null=True, blank=True)
    salary_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  
    address = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True) 
    is_associated = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

#####################-------------------------Bank Details
class BankDetails(models.Model):
    associated_employeer = models.ForeignKey(AssociatedEmployees, on_delete=models.CASCADE,null=True,blank=True)
    salaried_employee= models.ForeignKey('gigworkers.GigEmployee', on_delete=models.CASCADE,null=True,blank=True)
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=20, null=True, blank=True)
    account_holder_name = models.CharField(max_length=100, null=True, blank=True)
    branch_name = models.CharField(max_length=100, null=True, blank=True)
    upi_id=models.CharField(max_length=100, null=True, blank=True)
    ifsc_code = models.CharField(max_length=20, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


