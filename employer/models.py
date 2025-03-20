from django.db import models
from gigworkers.managers import *
from gigworkers.models import *
from datetime import timedelta
from django.utils import timezone
#################------------------------------Country Selectors----------------------- #################
class CountriesSelector(models.Model):
    country_choice=[
        ("India","India"),
        ("Uganda","Uganda"),
    ]
    country=models.CharField(max_length=200, choices=country_choice, default='India')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

#####################------------------------------------States--------------------#################
class StateMaster(models.Model):
    country = models.ForeignKey(CountriesSelector, on_delete=models.CASCADE, null=True, blank=True)
    state = models.CharField(null=True, blank=True, max_length=100)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
##################################--------------------District---------------------#############
class DistrictMaster(models.Model):
    state = models.ForeignKey(StateMaster, on_delete=models.CASCADE, null=True, blank=True)
    district=models.CharField(null=True, blank=True, max_length=100)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
#------------------------------EMPLOYERR MODELS
class Employeer(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=100,null=True, blank=True)
    company_profile=models.FileField(upload_to='employer/profile',null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=128)
    fcm_token = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=10, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_partnership = models.BooleanField(default=False)

#######################--------------------Employer Busienss Details
class EmployerBusinessDetails(models.Model):
    employer = models.ForeignKey(Employeer, on_delete=models.CASCADE,null=True,blank=True)
    business_location=models.CharField(max_length=128)
    business_type = models.CharField(max_length=100, choices=[
        ('Manufacturing', 'Manufacturing'),
        ('Retail', 'Retail'),
        ('Service', 'Service'),
        ('Agriculture', 'Agriculture'),
        ('Other', 'Other'),
    ], default='Other')
    business_description = models.TextField(null=True, blank=True)
    established_date = models.DateField(null=True, blank=True)
    registration_number = models.CharField(max_length=100, unique=True, null=True, blank=True)  
    gst_number = models.CharField(max_length=20, unique=True, null=True, blank=True) 
    country=models.ForeignKey(CountriesSelector, on_delete=models.CASCADE,null=True,blank=True)
    state=models.ForeignKey(StateMaster, on_delete=models.CASCADE,null=True,blank=True)
    district=models.ForeignKey(DistrictMaster, on_delete=models.CASCADE,null=True,blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
##################------------------------------Company Poilicses
class EmployerCompanyPolicies(models.Model):
    employer = models.ForeignKey(Employeer, on_delete=models.CASCADE, related_name="company_policies")
    notice_period_days = models.PositiveIntegerField(default=30)  # Notice period in days
    probation_period_days = models.PositiveIntegerField(default=90)  # Probation period in days
    total_annual_leaves = models.PositiveIntegerField(default=20)  # Total leaves per year
    sick_leaves = models.PositiveIntegerField(default=10)  # Sick leaves per year
    casual_leaves = models.PositiveIntegerField(default=10)  # Casual leaves per year
    maternity_leaves = models.PositiveIntegerField(default=90, null=True, blank=True)  # Maternity leave (if applicable)
    working_hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=8.00)  # Daily working hours
    overtime_policy = models.TextField(null=True, blank=True)  # Overtime payment or compensatory leave details
    resignation_policy = models.TextField(null=True, blank=True)  # Resignation & exit policy
    remote_work_policy = models.TextField(null=True, blank=True)  # WFH/Remote work rules
    other_policies = models.TextField(null=True, blank=True)  # Additional policies
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employer.company_name} - Company Policies"

    class Meta:
        verbose_name = "Company Policy"
        verbose_name_plural = "Company Policies"

########################----------------------Employer Emails Details
class EmployerEmailsDetails(models.Model):
    employer = models.ForeignKey(Employeer, on_delete=models.CASCADE,null=True,blank=True)
    EMAIL_TYPE_CHOICES = [
        ('HR', 'HR Email'),
        ('Communication', 'Communication Email'),
        ('Support', 'Support Email'),
        ('Finance', 'Finance Email'),
        ('Other', 'Other'),
    ]
    email = models.EmailField(max_length=100, null=True, blank=True)
    email_type = models.CharField(max_length=50, choices=EMAIL_TYPE_CHOICES, default='Other')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

############################---------------------------Employer Work Location------------
class EmployerWorkLocation(models.Model):
    employer = models.ForeignKey(Employeer, on_delete=models.CASCADE,null=True, blank=True)
    country=models.ForeignKey(CountriesSelector, on_delete=models.CASCADE,null=True,blank=True)
    state=models.ForeignKey(StateMaster, on_delete=models.CASCADE,null=True,blank=True)
    district=models.ForeignKey(DistrictMaster, on_delete=models.CASCADE,null=True,blank=True)
    total_employees=models.IntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

######################---------------------------Email OTP Models---------------####################
class EmailOtp(models.Model):
    email = models.EmailField(max_length=255, null=True, blank=True)
    mobile = models.CharField(null=True, blank=True, max_length=10, validators=[validate_mobile_no], unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at
    

###################---------------------Add Ratings by Employee
class RateEmployee(models.Model):
    employee = models.ForeignKey('gigworkers.GigEmployee', on_delete=models.CASCADE, null=True, blank=True, related_name='employer_ratings')
    employer = models.ForeignKey(Employeer, on_delete=models.CASCADE, null=True, blank=True, related_name='employee_ratings')
    description = models.CharField(max_length=100, null=True, blank=True)
    rating = models.IntegerField(default=0, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

