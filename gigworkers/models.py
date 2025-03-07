from django.db import models
from .managers import *
from django.utils import timezone
from employer.models import *
from decimal import Decimal,ROUND_HALF_UP

####---------------------------OTP Verification
class OTPVerification(models.Model):
    mobile = models.CharField(null=True, blank=True, max_length=10, validators=[validate_mobile_no], unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at
###############-------------------Employee Model (Salaried)------------------#########
class GigEmployee(models.Model):
    user=models.OneToOneField(CustomUser,on_delete=models.CASCADE,null=True,blank=True)
    associated_employees = models.ForeignKey('employer.AssociatedEmployees', on_delete=models.CASCADE,null=True, blank=True)
    assocated_employeer=models.ForeignKey('employer.Employeer',on_delete=models.CASCADE,null=True, blank=True)
    employee_id= models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=10, validators=[validate_mobile_no])
    gender=models.CharField(null=True, blank=True, max_length=100)
    dob = models.DateField(null=True, blank=True) 
    department = models.CharField(max_length=100, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True) 
    date_joined = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  
    salary_date = models.DateField(null=True, blank=True) ###----For AFFILATED
    payment_cycle = models.DateField(null=True, blank=True) ##---For Nong Affliated
    address = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    is_affilated = models.BooleanField(default=True)
    buy_franchise= models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} ({self.employee_id})"

    def get_age(self):
        """Calculate employee's age"""
        if self.dob:
            return (timezone.now().date() - self.dob).days // 365
        return None
    
    def is_eligible_for_ewa(self):
        """Check if the employee is eligible for Earned Wage Access (EWA)."""
        #------------- Check age criteria (21 - 55 years)
        age = self.get_age()
        print(f"Age is : {age} years old")

        if age is None or not (21 <= age <= 55):
            return False
        #------------------ Check job duration (12+ months)
        if not self.date_joined or self.date_joined > timezone.now().date() - timedelta(days=365):
            return False

        return True
    

####---------------------Employee Verifications
class EmployeeVerification(models.Model):
    employee = models.OneToOneField(GigEmployee, on_delete=models.CASCADE,null=True,blank=True)
    pan_number = models.CharField(max_length=10, unique=True, null=True, blank=True)
    pan_verified = models.BooleanField(default=False)
    aadhar_number = models.CharField(max_length=12, unique=True, null=True, blank=True)
    aadhar_image = models.ImageField(upload_to='employee/adhar', null=True, blank=True)
    aadhar_verified = models.BooleanField(default=False)
    selfie = models.ImageField(upload_to='employee/selfies', null=True, blank=True)
    video_kyc = models.FileField(upload_to='employee/video_kyc', null=True, blank=True)
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

        # Apply EWA Cap (50% - 70% of earned wages)
        min_cap = Decimal(0.5) * self.earned_wages  
        max_cap = Decimal(0.7) * self.earned_wages
        self.ewa_limit = max(min_cap, max_cap)
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
    upfront_interest = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def calculate_interest(self):
        """Calculate upfront interest based on employee type."""
        today = timezone.now().date()

        # Determine payday/payment cycle
        if self.employee.is_affilated == True:
            payday = self.employee.salary_date
            interest_rate = Decimal(0.004)  
        else:
            payday = self.employee.payment_cycle
            interest_rate = Decimal(0.006)  # 0.6% per week (gig worker)

        if not payday or payday < today:
            return Decimal(0)  # No interest if no valid payday

        # Calculate number of days until payday
        days_until_payday = (payday - today).days
        weeks_until_payday = Decimal(days_until_payday) / Decimal(7)
        upfront_interest = self.amount_requested * interest_rate * weeks_until_payday

        return round(upfront_interest, 2)

    def __str__(self):
        return f"{self.employee.name} - {self.amount_requested} ({self.status})"
    


############################3---------------------------Earn + Setup Fess PAYMENTS
class FranchiseSubscribed(models.Model):
    subscription_id = models.CharField(max_length=50, unique=True, editable=False)
    employee=models.ForeignKey(GigEmployee,on_delete=models.CASCADE,null=True,blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[('initiated', 'Initiated'), ('success', 'Success'), ('failed', 'Failed')],
        default='initiated'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at=models.DateTimeField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_signature_id = models.CharField(max_length=128,null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.subscription_id:
            base_subscription_id = f"SUB-{timezone.now().strftime('%Y%m%d')}-"
            latest_subscription_id = FranchiseSubscribed.objects.filter(created_at__date=timezone.now().date()).count()
            self.subscription_id = f"{base_subscription_id}{str(latest_subscription_id + 1).zfill(3)}"
            while FranchiseSubscribed.objects.filter(subscription_id=self.subscription_id).exists():
                latest_subscription_id += 1
                self.subscription_id = f"{base_subscription_id}{str(latest_subscription_id + 1).zfill(3)}"

        super().save(*args, **kwargs)

    def calculate_total_amount(self):
        """Calculate the total amount including GST."""
        gst_rate = 0.18  # 18% GST
        self.gst_amount = self.amount * gst_rate
        self.total_amount = (self.amount + self.gst_amount) - self.discount  

##########################----------------------------Notifications
class OrderNotifications(models.Model):
    NOTIFICATION_TYPES = [
        ('ewa','Earned Wage Access'),
        ('franchise','Franchise Notification'),
    ]
    employee = models.ForeignKey(GigEmployee, on_delete=models.CASCADE,null=True,blank=True)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES,null=True,blank=True)
    created_at=models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    
    
