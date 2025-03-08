from rest_framework import serializers
from .managers import *
from .models import *
from employer.models import *


class EmployeeRegistrationSerializer(serializers.ModelSerializer):
    mobile = serializers.CharField()
    user_type = serializers.ChoiceField(choices=['gigaff', 'nongigaff'])
    class Meta:
        model = CustomUser
        fields = ['mobile', 'user_type','employee_id']


    def create(self, validated_data):
        user_type = validated_data.get('user_type')
        mobile = validated_data.get('mobile')

        if not user_type:
            raise ValueError("user_type must be provided")
        user = CustomUser.objects.create_user(
            mobile=validated_data.get('mobile'),
            user_type=self.user_type
        )

        if self.user_type == 'gigaff':
            associated_employeer = AssociatedEmployees.objects.filter(phone_number=mobile).first()
            GigEmployee.objects.create(user=user, mobile=user.mobile,associated_employeer=associated_employeer,employee_id=associated_employeer.employee_id,
                                       name=associated_employeer.employee_name,assocated_employeer=associated_employeer.employeer,
                                       dob=associated_employeer.dob,date_joined=associated_employeer.date_joined,
                                       department=associated_employeer.department, designation=associated_employeer.designation,
                                       salary=associated_employeer.salary, address=associated_employeer.address,salary_date =associated_employeer.salary_date
                                       )
        else:
            raise ValueError("Invalid user type")

        print(f"Created {self.user_type} user: {user} with Mobile: {user.mobile}")
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