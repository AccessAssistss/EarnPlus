from rest_framework import serializers
from .managers import *
from .models import *
from associate.models import *
from employer.models import *
from django.db.models import Sum
#####################------------------------Gig Bank Details
#########################----------------------Add Employeee
class AddGigBankeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetails
        fields = ['id',
            'bank_name', 'account_number', 'account_holder_name', 'branch_name', 
            'upi_id', 'ifsc_code'
        ]
###################---------------------------Salaried Employee Details
class SalariedEmployeesSerializer(serializers.ModelSerializer):
    employer_name=serializers.CharField(source='employeer.name',allow_blank=True)
    employer_logo=serializers.CharField(source='employeer.company_profile',allow_null=True)
    total_salary_thismonth=serializers.SerializerMethodField()
    class Meta:
        model=GigEmployee
        fields=['id','employee_id','employer_name','employer_logo','employee_name','total_salary_thismonth']

    def get_total_salary_thismonth(self,obj):
        current_month=timezone.now().month
        print(f"Curentr Mointh is :{current_month}")
        current_year=timezone.now().year
        print(f"Curentr Year :{current_year}")
        total_salary=SalaryHistory.objects.filter(employee=obj,salary_date__year=current_year,
                                                  salary_date__month=current_month).aggregate(Sum('daily_salary'))['daily_salary__sum'] or 0
        return total_salary
#################--------------------------Non SALARIED eMPLOYABILITY ADD

class AddnonEmployeeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    class Meta:
        model = GigEmployee
        fields = ['id',
            'employee_name', 'employee_id', 'email', 'phone_number', 
            'designation', 'dob', 'department', 'date_joined', 
            'salary', 'address'
        ]
    
############---------------------------Employee VERIFICATIONS
class EmployeeVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeVerification
        fields = ['pan_number', 'aadhar_number', 'selfie', 'video_kyc', 'is_verified']
        
################------------------Slots by Associates-------------###########
class AssociatesSlotSerializer(serializers.ModelSerializer):
    slot = serializers.SerializerMethodField()
    slot_id=serializers.SerializerMethodField()
    weeks=serializers.SerializerMethodField()
    class Meta:
        model = AddAssoicateBookingSlots
        fields = ["id", "slot","slot_id","weeks"]

    def get_slot(self, obj):
        return obj.slot.slot if obj.slot else None
    def get_slot_id(self, obj):
        return obj.slot.id if obj.slot else None
    def get_weeks(self,obj):
        return obj.slot.day_weeks if obj.slot else None

###########################-----------------Salary Histories
class SalaryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryHistory
        fields = ['id',
            'employee',
            'salary_date',
            'daily_salary',
        ]

##################------------------Employeer List---------------------##############
class EmployeerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employeer
        fields = ['id', 'name','company_profile']

##################------------------Employee List---------------------##############

class EWATransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EWATransaction
        fields = ['id',
            'transaction_id',
            'amount',
            'withdrawal_date',
            'due_date',
            'interest_rate',
            'interest_amount',
            'total_payable',
            'status',
            'repayment_status',
        ]