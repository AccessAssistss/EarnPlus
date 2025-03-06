from django.db import models
from .managers import *
from django.utils import timezone
from employer.models import *
from decimal import Decimal

####---------------------------OTP Verification
class OTPVerification(models.Model):
    mobile = models.CharField(null=True, blank=True, max_length=10, validators=[validate_mobile_no], unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at
###############-------------------Employee Model
class GigEmployee(models.Model):
    user=models.OneToOneField(CustomUser,on_delete=models.CASCADE,null=True,blank=True)
    associated_employeer = models.ForeignKey('employer.Employeer', on_delete=models.CASCADE,null=True, blank=True)
    employee_id= models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=10, validators=[validate_mobile_no])
    gender=models.CharField(null=True, blank=True, max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    
    def is_eligible_for_ewa(self):
        """Check if the employee is eligible for EWA."""
        associated_employee = self.associated_employeer
        if not associated_employee:
            return False

        #-------------Check age criteria (21 - 55 years)
        age = associated_employee.get_age()
        if age is None or age < 21 or age > 55:
            return False

        #------------------Check job duration (12+ months) and not on probation
        if not associated_employee.date_joined or associated_employee.date_joined > timezone.now().date() - timedelta(days=365):
            return False

        return True
    
    

####---------------------Employee Verifications
class EmployeeVerification(models.Model):
    employee = models.OneToOneField(GigEmployee, on_delete=models.CASCADE,null=True,blank=True)
    pan_number = models.CharField(max_length=10, unique=True, null=True, blank=True)
    aadhar_number = models.CharField(max_length=12, unique=True, null=True, blank=True)
    selfie = models.ImageField(upload_to='selfies/', null=True, blank=True)
    video_kyc = models.FileField(upload_to='video_kyc/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

###############-----------------------Employee Salary History
class SalaryHistory(models.Model):
    """Tracks past salaries and payments for employees"""
    employee = models.ForeignKey(GigEmployee, on_delete=models.CASCADE,null=True,blank=True)
    salary_amount = models.DecimalField(max_digits=10, decimal_places=2) 
    start_date = models.DateField()  
    end_date = models.DateField()  
    days_paid = models.IntegerField()  
    created_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return f"{self.employee.name} - {self.start_date} to {self.end_date}"
# ------------------------------ Salary Details Model
class SalaryDetails(models.Model):
    employee = models.OneToOneField(GigEmployee, on_delete=models.CASCADE,null=True,blank=True)
    salary_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    employment_status = models.CharField(max_length=50, choices=[("active", "Active"), ("inactive", "Inactive")])
    last_salary_date = models.DateField(null=True, blank=True)  # Last salary paid date
    daily_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Salary per day
    earned_wages = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Wages earned till now
    ewa_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    def calculate_earned_wages(self):
        """Calculate earned wages based on the days worked since last salary."""
        if not self.last_salary_date:
            return 0 

        days_worked = (timezone.now().date() - self.last_salary_date).days
        self.earned_wages = self.daily_salary * days_worked
        self.ewa_limit = self.earned_wages  
        #---------------Apply EWA cap (between 50% - 70% of earned wages)
        min_cap = Decimal(0.5) * self.earned_wages  
        max_cap = Decimal(0.7) * self.earned_wages
        self.ewa_limit = max(min_cap, min(self.requested_ewa, max_cap))
        self.save()
        return self.earned_wages

    def __str__(self):
        return f"Salary for {self.employee.name} - {self.salary_amount}"
###############################----------------EWA Requests   
class EWARequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("disbursed", "Disbursed"),
    ]
    loan_choices = [
        ("Emeregency Finance","Emeregency Finance"),
        ("Bridge Finance","Bridge Finance"),
        ("Liquidity Finance","Liquidity Finance"),
    ]
    employee = models.ForeignKey(GigEmployee, on_delete=models.CASCADE,null=True,blank=True)
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    loan_type = models.CharField(max_length=50, choices=loan_choices, default="Emeregency Finance")
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    #processed_by = models.ForeignKey('loanadmin.LoanAdmin', on_delete=models.SET_NULL, null=True, blank=True, related_name="processed_ewa_requests")

    def __str__(self):
        return f"{self.employee.name} - {self.amount_requested} ({self.status})"
    
    
