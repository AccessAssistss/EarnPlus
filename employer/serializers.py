from rest_framework import status
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from gigworkers.managers import CustomUser
from rest_framework.response import Response
from .models import *
from gigworkers.models import *
################-------------------------Employeer Registration
class EmployerRegistrationSerializer(serializers.Serializer):
    mobile = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=['employer'])
    name = serializers.CharField(required=False)

    def create(self, validated_data):
        user_type = validated_data['user_type']
        name = validated_data.pop('name', None)
        user = CustomUser.objects.create_user(
            mobile=validated_data['mobile'],
            password=validated_data['password'],
            user_type=user_type,
            name=name,
            email=validated_data['email']
        )
        if user_type == 'employer':
            if not name:
                raise serializers.ValidationError({"name": "Name is required for employerr users."})
            Employeer.objects.create(user=user, mobile=user.mobile,name=name,password=user.password,
                                    email=user.email)
        else:
            user.delete()  
            raise serializers.ValidationError({"user_type": "Invalid user type."})
        
        

        print(f"Created {user_type} user: {user}")
        return user

    def validate(self, data):
        user_type = data.get('user_type')
        name = data.get('name')
        print(f"Validating {user_type} Validation Name: {name}")

        if user_type in ['employer'] and not name:
            raise serializers.ValidationError({"name": f"Name is required for {user_type.upper()} users."})

        return data
    

#############################--------------------------Add Employee By Employers
class AddEmployeeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    mobile = serializers.CharField(required=True)

    class Meta:
        model = GigEmployee
        fields = [
            'id', 'employee_name', 'employee_id', 'email', 'mobile', 
            'designation', 'dob', 'department', 'date_joined', 'employment_type', 
            'payment_cycle', 'address'
        ]

    def validate(self, data):
        """Check if mobile or employee_id already exists and return a structured error response."""
        if CustomUser.objects.filter(username=data.get('mobile')).exists():
            raise serializers.ValidationError({"error": "A user with this mobile number already exists."})

        if GigEmployee.objects.filter(employee_id=data.get('employee_id')).exists():
            raise serializers.ValidationError({"error": "An employee with this ID already exists."})

        return data

    def create(self, validated_data):
        """
        Override create method to first create a CustomUser and then associate it with GigEmployee.
        """
        #---------------Extract fields
        email = validated_data.get('email', None)
        mobile = validated_data.get('mobile')

        #-----------Create CustomUser instance
        user = CustomUser.objects.create_user(
            mobile=mobile,  
            email=email,
            user_type="gigaff"  
        )
        gig_employee = GigEmployee.objects.create(user=user, **validated_data)
        return gig_employee
######################---------------------Employeer Login----------------------------
class EmployerLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=['employer'])


######------------------------Employerr Details
class EmployerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employeer
        fields = ['id','name', 'company_profile', 'email', 'mobile', 'fcm_token', 'is_deleted', 'is_partnership']

        extra_kwargs = {
            'company_profile': {'required': False},
            'email': {'read_only': True},  
            'mobile': {'read_only': True},
            'fcm_token': {'read_only': True},
            'is_deleted': {'read_only': True},
            'is_partnership': {'read_only': True},
        }
      

###########################-----------------Salary Histories
class EmployeeSalaryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryHistory
        fields = ['id',
            'employee',
            'salary_date',
            'daily_salary',
        ]
