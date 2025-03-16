from django.utils import timezone
from django.contrib.auth.hashers import make_password
from rest_framework import status
from rest_framework.test import APITestCase
from gigworkers.managers import CustomUser
from .models import EmailOtp

###################3--------------------Employer Auth Module-------------------###############
class EmployerAuth(APITestCase):
    def setUp(self):
        self.registration_url=""
        self.login_url=""
        self.password_request_url=""
        self.password_reset_url=""
        self.user_data={
            "name": "test_employer",
            "email": "test_employer@example.com",
            "mobile":"9111111111",
            "password": "test123",
            "phone_number": "1234567890",
            "user_type": "employer"
        }
        self.user=CustomUser.objects.create (ame=self.user_data["name"],
            email=self.user_data["email"],
            mobile=self.user_data["mobile"],
            password=make_password(self.user_data["password"]),
            user_type=self.user_data["user_type"])
        
    def test_registration_success(self):
        response = self.client.post(self.registration_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)

    def test_registration_duplicate_user(self):
        CustomUser.objects.create(**self.user_data)
        response = self.client.post(self.registration_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)