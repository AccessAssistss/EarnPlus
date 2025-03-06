from rest_framework import status
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from gigworkers.managers import CustomUser
from rest_framework.response import Response
from .models import *
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
######################---------------------Employeer Login----------------------------
class EmployerLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=['employer'])

#########################----------------------Add Employeee
class AddEmployeeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    class Meta:
        model = AssociatedEmployees
        fields = ['id',
            'employee_name', 'employee_id', 'email', 'phone_number', 
            'designation', 'dob', 'department', 'date_joined', 
            'salary', 'address'
        ]
    
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
      