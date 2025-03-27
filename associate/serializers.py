from rest_framework import status
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from gigworkers.managers import CustomUser
from rest_framework.response import Response
from .models import *
from gigworkers.models import *
from django.contrib.auth.hashers import make_password
from employer.serializers import AddEmployeeSerializer
################-------------------------Employeer Registration
class AssociateRegistrationSerializer(serializers.Serializer):
    mobile = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=['associate'])
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
        if user_type == 'associate':
            if not name:
                raise serializers.ValidationError({"name": "Name is required for employerr users."})
            Associate.objects.create(user=user, mobile=user.mobile,name=name,password=user.password,
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

        if user_type in ['associate'] and not name:
            raise serializers.ValidationError({"name": f"Name is required for {user_type.upper()} users."})

        return data
######----------------------------------Emploeyr ASSOCIATE rEGSIATRTION------------------############
class AssociateEmployerRegistrationSerializer(serializers.Serializer):
    mobile = serializers.CharField()
    email = serializers.EmailField()
    name = serializers.CharField(required=False)
    

    def create(self, validated_data):
        name = validated_data.pop('name', None)
        request = self.context.get('request') 
        user_type="employer"
        default_password = make_password("Admin@1234")
        associate = Associate.objects.filter(user=request.user).first()
        user = CustomUser.objects.create_user(
            mobile=validated_data['mobile'],
            password=default_password,
            user_type=user_type,
            name=name,
            email=validated_data['email']
        )
        Employeer.objects.create(user=user, mobile=user.mobile,name=name,password=user.password,
                                email=user.email,associate=associate)
        
        
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
class AssociateLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=['associate'])
    
####################------------------Associate Slots
#############----------------Booking Slots
class AssociateSlotsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddAssoicateBookingSlots
        fields = "__all__"
#############----------------Booking Slots
class BookSlotsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingSlots
        fields = "__all__"
#######################-----------------------EmployerAssociated------------------#############
class AssociatedEmployers(serializers.ModelSerializer):
    class Meta:
        model=Employeer
        fields=['id','name','email','mobile','is_active']
####################-----------------------Book Kyc-------------------###########
class BookKycSerializer(serializers.ModelSerializer):
    employee=AddEmployeeSerializer(read_only=True)
    class Meta:
        model = BookkycEmployee
        fields = ['id','slot','slot_date','meet_link','employee']