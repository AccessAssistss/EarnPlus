from django.db import models
from .managers import *
from django.utils import timezone
from employer.models import *
from decimal import Decimal
import uuid

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
    associated_employeer=models.ForeignKey('employer.Employeer',on_delete=models.CASCADE,null=True, blank=True)
    employee_id= models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=10, validators=[validate_mobile_no])
    gender=models.CharField(null=True, blank=True, max_length=100)
    fcm_token=models.CharField(null=True, blank=True, max_length=100)
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
    is_employer_screen = models.BooleanField(default=False)
    is_affilated = models.BooleanField(default=True)
    buy_franchise= models.BooleanField(default=False)
    is_on_probation = models.BooleanField(default=False)
    has_default_history = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} ({self.employee_id})"

    def get_age(self):
        """Calculate employee's age"""
        if self.dob:
            return (timezone.now().date() - self.dob).days // 365
        return None
    
    def is_eligible_for_ewa(self):
        """Check if the employee is eligible for Earned Wage Access (EWA)."""
        age = self.get_age()
        if age is None or not (21 <= age <= 55):
            return False
        if not self.date_joined or self.date_joined > timezone.now().date() - timedelta(days=365):
            return False
        if self.is_on_probation or self.has_default_history:
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
    selfie_verified =models.BooleanField(default=False)
    video_kyc = models.FileField(upload_to='employee/video_kyc', null=True, blank=True)
    video_verified =models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


###############-----------------------Employee Salary History
class SalaryHistory(models.Model):
    """Tracks past salaries and payments for employees"""
    employee = models.ForeignKey(GigEmployee, on_delete=models.CASCADE,null=True,blank=True)
    daily_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Salary per day
    salary_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)  

class SalaryDetails(models.Model):
    employee = models.OneToOneField(GigEmployee, on_delete=models.CASCADE, null=True, blank=True)
    earned_wages = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Wages earned till now
    ewa_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Current EWA limit
    last_withdrawal_date = models.DateField(null=True, blank=True)  # Track the last withdrawal date
    last_withdrawal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Track the last withdrawal amount
    last_updated = models.DateTimeField(auto_now=True)  # Timestamp when the record was last updated

    def get_daily_salary_records(self, start_date, end_date):
        """Fetch daily salary records for the employee between two dates."""
        return SalaryHistory.objects.filter(
            employee=self.employee,
            salary_date__gte=start_date,
            salary_date__lte=end_date
        )

    def calculate_earned_wages(self):
        """Calculate earned wages based on daily salary data since the last salary or withdrawal."""
        if self.last_withdrawal_date:
            start_date = self.last_withdrawal_date
        else:
            last_salary_record = SalaryHistory.objects.filter(
                employee=self.employee,
                daily_salary__gt=0  
            ).order_by('-salary_date').first()
            print(f"Last salary record :{last_salary_record}")
            if not last_salary_record:
                return 0
            start_date = last_salary_record.salary_date
            print(f"Salary START dATE :{start_date}")

        #------------Fetch daily salary records since the start date
        daily_salary_records = self.get_daily_salary_records(start_date, timezone.now().date())
        print(f"Daily salary records :{daily_salary_records}")

        #----------------Calculate earned wages
        self.earned_wages = sum(record.daily_salary for record in daily_salary_records)
        ew=self.earned_wages
        print(f"Earned Wages :{ew}")

        #--------------Apply EWA Cap (50% - 70% of earned wages)
        min_cap = Decimal('0.5') * self.earned_wages
        max_cap = Decimal('0.7') * self.earned_wages
        self.ewa_limit = max(min_cap, max_cap)

        self.save()
        return self.earned_wages


    def update_ewa_limit_after_withdrawal(self, withdrawal_amount):
        """Update the EWA limit after a withdrawal."""
        if withdrawal_amount > self.ewa_limit:
            raise ValueError("Withdrawal amount exceeds EWA limit")

        #---------------Deduct the withdrawal amount from the EWA limit
        self.ewa_limit -= withdrawal_amount
        self.last_withdrawal_amount = withdrawal_amount
        self.last_withdrawal_date = timezone.now().date()
        self.save()

    def __str__(self):
        return f"Salary Details for {self.employee.name}"

    def calculate_due_date(self):
        """
        Calculate the due date for EWA repayment based on salary payment cycle
        """
        #-------------------For employees with fixed monthly salary
        employee=self.employee
        if employee.is_affilated():
            return employee.payment_cycle
        else:
            #-------------------------------Maximum 30 days
            return timezone.now().date() + timedelta(days=30)

    def __str__(self):
        return f"Salary for {self.employee.name} - {self.salary_amount}"

###############################----------------EWA Requests   
class EWATransaction(models.Model):
    loan_choices = [
        ("Emeregency Finance","Emeregency Finance"),
        ("Bridge Finance","Bridge Finance"),
        ("Liquidity Finance","Liquidity Finance"),
    ]
    employee = models.ForeignKey(GigEmployee, on_delete=models.CASCADE,null=True,blank=True)
    loan_type = models.CharField(max_length=50, choices=loan_choices, default="Emeregency Finance")
    STATUS_CHOICES = (
        ('INITIATED', 'Initiated'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )
    
    REPAYMENT_STATUS = (
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Fully Paid'),
        ('OVERDUE', 'Overdue'),
    )
    
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    employee = models.ForeignKey(GigEmployee, on_delete=models.CASCADE, related_name='ewa_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    withdrawal_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.4)  # 0.4% per week
    interest_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_payable = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INITIATED')
    repayment_status = models.CharField(max_length=20, choices=REPAYMENT_STATUS, default='PENDING')
    
    #------------------Payment details
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"EWA Transaction: {self.employee.name} - ₹{self.amount} - {self.status}"

    def calculate_interest(self):
        """Calculate interest based on 0.4% per week"""
        if not self.due_date:
            return 0
            
        days_until_due = (self.due_date - self.withdrawal_date.date()).days
        weeks = days_until_due / 7  # Convert days to weeks
        
        interest = round(self.amount * (self.interest_rate / 100) * weeks, 2)
        print(f"Interest is :{interest}")
        self.interest_amount = interest
        self.total_payable = self.amount + interest
        print(f"Total Payable amount is :{self.total_payable}")
        self.save()
        
        return self.interest_amount
    

# ------------------------------ EWA Repayment Model
class EWARepayment(models.Model):
    transaction = models.ForeignKey(EWATransaction, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, default='RAZORPAY')
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return f"Repayment: {self.transaction.transaction_id} - ₹{self.amount}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update transaction repayment status
        self.update_transaction_status()
    
    def update_transaction_status(self):
        """Update the transaction's repayment status based on total repayments"""
        transaction = self.transaction
        
        # Get total repaid amount
        total_repaid = sum(payment.amount for payment in transaction.repayments.all())
        
        if total_repaid >= transaction.total_payable:
            transaction.repayment_status = 'PAID'
        elif total_repaid > 0:
            transaction.repayment_status = 'PARTIAL'
        elif transaction.due_date < timezone.now().date():
            transaction.repayment_status = 'OVERDUE'
        else:
            transaction.repayment_status = 'PENDING'
            
        transaction.save()
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
    
    
