from django.db import models
from .managers import *
from django.utils import timezone
from datetime import timedelta
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
    employeer=models.ForeignKey('employer.Employeer',on_delete=models.CASCADE,null=True, blank=True)
    EMPLOYMENT_TYPE_CHOICES = [
        ('SALARIED', 'Salaried Employee'),
        ('CONTRACTUAL_FIXED_VARIABLE', 'Contractual with Fixed & Variable Salary'),
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
    employee_id= models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=10, validators=[validate_mobile_no])
    gender=models.CharField(null=True, blank=True, max_length=100)
    fcm_token=models.CharField(null=True, blank=True, max_length=100)
    dob = models.DateField(null=True, blank=True) 
    department = models.CharField(max_length=100, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True) 
    date_joined = models.DateField(null=True, blank=True)
    hire_date=models.DateField(null=True, blank=True)  
    salary_date = models.DateField(null=True, blank=True) ###----For AFFILATED
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
        return f"{self.employee_name} ({self.employee_id})"

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
    def get_ewa_cap_percentage(self):
        """Get the EWA cap percentage based on worker type."""
        if self.is_affilated:
            #---------Employees: 50%-70% of earned wages
            return (Decimal('0.5'), Decimal('0.7'))
        else:
            #-------------Gig Workers: 40%-70% of accrued income
            return (Decimal('0.4'), Decimal('0.7'))
    
    def get_daily_rate(self):
        """Calculate daily rate based on monthly salary."""
        if self.salary:
            return self.salary / Decimal('30')
        return Decimal('0')
    
    def calculate_next_payment_date(self):
        """Calculate the next payment date based on payment cycle."""
        if self.is_affilated and self.salary_date:
            #------------For affiliated employees with fixed salary date
            today = timezone.now().date()
            next_date = self.salary_date.replace(month=today.month)
            if next_date < today:
                if today.month == 12:
                    next_date = next_date.replace(year=today.year+1, month=1)
                else:
                    next_date = next_date.replace(month=today.month+1)
            return next_date
        else:
            #-------------For non-affiliated workers with variable payment cycle
            return timezone.now().date() + timedelta(days=self.payment_cycle)

######################--------------Employment Info
class EmploymentInfo(models.Model):
    employee=models.ForeignKey(GigEmployee,on_delete=models.CASCADE,null=True,blank=True)
    hire_date=models.DateField(null=True, blank=True)
    joining_date=models.DateField(null=True, blank=True)
    basic_salary=models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
#####################-------------------------Bank Details
class BankDetails(models.Model):
    salaried_employee= models.ForeignKey(GigEmployee, on_delete=models.CASCADE,null=True,blank=True)
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=20, null=True, blank=True)
    account_holder_name = models.CharField(max_length=100, null=True, blank=True)
    branch_name = models.CharField(max_length=100, null=True, blank=True)
    upi_id=models.CharField(max_length=100, null=True, blank=True)
    ifsc_code = models.CharField(max_length=20, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    """Tracks past salaries and payments for employees Salaried Payment Cycle monthly"""
    employee = models.ForeignKey(GigEmployee, on_delete=models.CASCADE,null=True,blank=True)
    employer = models.ForeignKey('employer.Employeer', on_delete=models.CASCADE,null=True,blank=True)
    daily_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Salary per day Fixed
    salary_date = models.DateField()
    """Addition Field for Fixed Daily Salary and Variable Income for Contarctual Fixed+Variable"""
    products_produced = models.IntegerField(default=0)  # Number of products produced
    variable_income = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    rate_per_product = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Rate per product
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Fixed + Variable
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True) 

    def save(self, *args, **kwargs):
        self.variable_income = self.products_produced * self.rate_per_product
        self.total_earnings = self.daily_salary + self.variable_income
        
        super().save(*args, **kwargs)

class SalaryDetails(models.Model):
    employee = models.OneToOneField(GigEmployee, on_delete=models.CASCADE, null=True, blank=True)
    earned_wages = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Wages earned till now
    ewa_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Current EWA limit
    last_withdrawal_date = models.DateField(null=True, blank=True)  # Track the last withdrawal date
    last_withdrawal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Track the last withdrawal amount
    created_at = models.DateTimeField(auto_now_add=True)
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
            print(f"Using last withdrawal date as start: {start_date}")
        else:
            first_salary_record = SalaryHistory.objects.filter(
                employee=self.employee,
                total_earnings__gt=0  
            ).order_by('salary_date').first()  #----------------Fetch the earliest record

            if not first_salary_record:
                print("No salary records found.")
                return 0

            start_date = first_salary_record.salary_date  # Start from the earliest date
            print(f"Using first salary record as start: {start_date}")

        #---------------Fetch daily salary records since start_date
        daily_salary_records = list(self.get_daily_salary_records(start_date, timezone.now().date()))
        print(f"Filtered Daily Salary Records: {[(record.salary_date, record.total_earnings) for record in daily_salary_records]}")

        #------------------Calculate total earned wages
        self.earned_wages = sum(record.total_earnings for record in daily_salary_records)
        print(f"Earned Wages: {self.earned_wages}")

        #------------------Get EWA cap percentages from the employee model
        min_cap_pct, max_cap_pct = self.employee.get_ewa_cap_percentage()
        
        #---------------Calculate min and max caps
        min_cap = min_cap_pct * self.earned_wages
        max_cap = max_cap_pct * self.earned_wages
        print(f"Min Cap: {min_cap}, Max Cap: {max_cap}")

        #-------------------Set EWA limit to max cap but not exceeding earned wages
        self.ewa_limit = min(max_cap, self.earned_wages)  
        print(f"Updated EWA Limit: {self.ewa_limit}")

        self.save()


    def update_ewa_limit_after_withdrawal(self, withdrawal_amount):
        """Update the EWA limit after a withdrawal."""
        if withdrawal_amount > self.ewa_limit:
            raise ValueError("Withdrawal amount exceeds EWA limit")

        #---------------Deduct the withdrawal amount from the EWA limit
        self.ewa_limit -= withdrawal_amount
        print(f"Updated EWA Limit: {self.ewa_limit}")
        self.last_withdrawal_amount = withdrawal_amount
        print(f"Withdrwal Amount : {self.last_withdrawal_amount}")
        self.last_withdrawal_date = timezone.now().date()
        print(f"Withdrwal Last DAte : {self.last_withdrawal_date}")
        self.save()

    def __str__(self):
        return f"Salary Details for {self.employee.employee_name}"

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
        return f"Salary for {self.employee.employee_name}"

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
    INTEREST_CHARGING_METHOD = (
        ('PRE_UTILIZATION', 'Pre-Utilization'),
        ('POST_UTILIZATION', 'Post-Utilization'),
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
    interest_charging_method = models.CharField(max_length=20, choices=INTEREST_CHARGING_METHOD, default='POST_UTILIZATION')
    
    #------------------Payment details
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"EWA Transaction: {self.employee.employee_name} - ₹{self.amount} - {self.status}"

    def calculate_interest(self):
        """Calculate interest based on daily interest rate"""
        if not self.due_date:
            return 0
            
        days_until_due = (self.due_date - self.withdrawal_date.date()).days
        print(f"Intersyt is {days_until_due}")
        
        #----------------Calculate interest based on daily rate
        interest = round(self.amount * self.interest_rate * days_until_due, 2)
        print(f"Intersyt is {interest}")
        self.interest_amount = interest
        
        if self.interest_charging_method == 'PRE_UTILIZATION':
            #---------------Deduct interest upfront
            self.prepaid_interest = interest
            self.total_payable = self.amount  # User only needs to repay principal
        else:
            #----------------------------POST_UTILIZATION - interest charged at repayment
            self.prepaid_interest = Decimal('0')
            self.total_payable = self.amount + interest
            
        self.save()
        return self.interest_amount
    
    def calculate_early_repayment_refund(self, repayment_date):
        """Calculate interest refund if paid early (for PRE_UTILIZATION charging)"""
        if self.interest_charging_method != 'PRE_UTILIZATION' or repayment_date >= self.due_date:
            return 0
            
        #---------------------------Calculate unused days
        unused_days = (self.due_date - repayment_date).days
        print(f"Unused Days :{unused_days}")
        
        #------------------------Calculate interest for unused days
        refund = round(self.amount * self.interest_rate * unused_days, 2)
        print(f"Refunc :{refund}")
        
        # Cannot refund more than pre-paid
        return min(refund, self.prepaid_interest)
    def is_eligible_for_withdraw(self):
        """Check if the transaction is eligible for withdrawal based on employee eligibility and EWA limit"""
        if not self.employee.is_eligible_for_ewa():
            return False
            
        #---------------------Check if the withdrawal amount is within the EWA limit
        try:
            salary_details = SalaryDetails.objects.get(employee=self.employee)
            return self.amount <= salary_details.ewa_limit
        except SalaryDetails.DoesNotExist:
            return False
        
#######################-----------------------EWA DAily Interst Amount Logs-----------------###############        
class EWAInterestLog(models.Model):
    """Tracks daily interest charges and other events for EWA transactions."""
    transaction = models.ForeignKey(EWATransaction, on_delete=models.CASCADE, related_name='interest_logs')
    event_type = models.CharField(max_length=50, choices=[
        ('DAILY_INTEREST', 'Daily Interest Charge'),
        ('REPAYMENT', 'Repayment'),
        ('REFUND', 'Refund'),
        ('OVERDUE_INTEREST', 'Overdue Interest Charge'),
    ])
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Amount charged or refunded
    event_date = models.DateField()  # Date of the event
    description = models.TextField(null=True, blank=True)  # Additional details
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} for {self.transaction.transaction_id} on {self.event_date}: ₹{self.amount}"
# ------------------------------ EWA Repayment Model
class EWARepayment(models.Model):
    transaction = models.ForeignKey(EWATransaction, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, default='RAZORPAY')
    interest_refund = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
        
        # Get total repaid amount (including any refunded interest for pre-utilization charging)
        total_repaid = sum(payment.amount for payment in transaction.repayments.all())
        total_refunded = sum(payment.interest_refund for payment in transaction.repayments.all())
        
        effective_payable = transaction.total_payable - total_refunded
        
        if total_repaid >= effective_payable:
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
    
    
