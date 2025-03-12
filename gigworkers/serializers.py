from rest_framework import serializers
from .managers import *
from .models import *
from employer.models import *


class EmployeeRegistrationSerializer(serializers.ModelSerializer):
    mobile = serializers.CharField()
    user_type = serializers.ChoiceField(choices=['gigaff', 'nongigaff'])
    class Meta:
        model = CustomUser
        fields = ['mobile', 'user_type']


    def create(self, validated_data):
        user_type = validated_data.get('user_type')
        mobile = validated_data.get('mobile')
        if not user_type:
            raise ValueError("user_type must be provided")
        user = CustomUser.objects.create_user(
            mobile=validated_data.get('mobile'),
            user_type=user_type
        )
        associated_employee = AssociatedEmployees.objects.filter(phone_number=mobile).first()
        GigEmployee.objects.create(
            user=user,
            mobile=user.mobile,
            associated_employees=associated_employee,
            associated_employeer=associated_employee.employeer if associated_employee else None,
            employee_id=associated_employee.employee_id if associated_employee else None,
            name=associated_employee.employee_name if associated_employee else None,
            dob=associated_employee.dob if associated_employee else None,
            date_joined=associated_employee.date_joined if associated_employee else None,
            department=associated_employee.department if associated_employee else None,
            designation=associated_employee.designation if associated_employee else None,
            salary=associated_employee.salary if associated_employee else None,
            address=associated_employee.address if associated_employee else None,
            salary_date=associated_employee.salary_date if associated_employee else None
        )
        return user

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
    employer_name=serializers.CharField(source='assocated_employeer.name',allow_blank=True)
    employer_logo=serializers.CharField(source='assocated_employeer.company_profile',allow_blank=True)
    class Meta:
        model=GigEmployee
        fields=['id','employee_id','employer_name','employer_logo','name']
#################--------------------------Non SALARIED eMPLOYABILITY ADD

class AddnonEmployeeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    class Meta:
        model = AssociatedEmployees
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