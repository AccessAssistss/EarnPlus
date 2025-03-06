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

    def __init__(self, *args, **kwargs):
        self.user_type = kwargs.pop('user_type', None)
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        if self.user_type is None:
            raise ValueError("user_type must be provided")
        user = CustomUser.objects.create_user(
            mobile=validated_data.get('mobile'),
            user_type=self.user_type
        )

        if self.user_type == 'gigaff':
            GigEmployee.objects.create(user=user, mobile=user.mobile)
        else:
            raise ValueError("Invalid user type")

        print(f"Created {self.user_type} user: {user} with Mobile: {user.mobile}")
        return user
    

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