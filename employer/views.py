from django.shortcuts import render
from gigworkers.utils import *
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
import random
from django.contrib.auth.hashers import check_password,make_password
from gigworkers.managers import *
from django.shortcuts import get_object_or_404
from gigworkers.models import *
from .models import *
from .serializers import *
from django.db.models import Q

# Create your views here.
###############---------------Authorization
##----------1.User Registration
class EmployerRegistration(APIView):
    permission_classes = [AllowAny]
    def post(self, request, format=None):
        user_type = request.data.get('user_type')
        mobile = request.data.get('mobile')
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name')
        ip_address = request.META.get('REMOTE_ADDR')
        print(f"Registration attempt with mobile: {mobile}, user_type: {user_type}, password: {password}, IP address: {ip_address}")
        try:
            user = CustomUser.objects.filter(
            Q(email=email, user_type=user_type) | Q(mobile=mobile, user_type=user_type)
            ).exists()
            print(f"User is :{user}")
            if user:
                return Response({'error': 'User with this mobile number already exists'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = EmployerRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e,"An error occured while registration")
            
####################-------------------------------------REST API's Login----------------###############
class EmployerLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = EmployerLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user_type = serializer.validated_data['user_type']
        ip_address = request.META.get('REMOTE_ADDR')

        print(f"Login attempt with email: {email}, user_type: {user_type}, IP address: {ip_address}")

        try:
            user = CustomUser.objects.filter(email=email, user_type=user_type).first()

            if not user:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            if check_password(password, user.password):
                tokens = create_gig_token(user, user_type)
                return Response({
                    'message': "User logged in successfully",
                    'tokens': tokens
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            return handle_exception(e,"An error occured while LOgin")
        
class FCMTokenView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        if user.user_type != 'employer':
            return Response({'status': 'error', 'message': 'User type is not Vednor'}, status=status.HTTP_400_BAD_REQUEST)

        fcm_token = request.data.get('fcm_token')

        if not fcm_token:
            return Response({'status': 'error', 'message': 'FCM token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            farmer_profile = Employeer.objects.get(user=user)
            farmer_profile.fcm_token = fcm_token
            farmer_profile.save()
            return Response({'status': 'success', 'message': 'FCM token saved successfully'}, status=status.HTTP_200_OK)
        except Employeer.DoesNotExist:
            return Response({'status': 'error', 'message': 'Vednor profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        
####--------------------------------Token Checker
class TockenChecker(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,format=None):
        user=request.user
        print(f"User is {user.user_type}")
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        print(f"Access token is {provided_access_token}")
        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!="employer":
            return Response({'error': 'User type is not Vednor'}, status=status.HTTP_400_BAD_REQUEST)
        token=request.query_params.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employer=get_object_or_404(Employeer,user=user)
            access_token=employer.user.access_token
            return Response({'status': token == access_token}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e,"An error occured while Checking Token")
        
        
##############------------------------Passoword
        
class PasswordResetRequestAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        user_type = request.data.get('user_type') 
        otp=request.data.get('otp')
        try:
            if not email or not user_type:
                return Response({'error': 'Email and user type are required.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = CustomUser.objects.get(email=email, user_type=user_type)
            except CustomUser.DoesNotExist:
                return Response({'error': 'User with this email and user type does not exist.'}, status=status.HTTP_404_NOT_FOUND)

            #otp = random.randint(100000, 999999)
            #print(f"Generated OTP: {otp}")
            store_emailotp(email,otp)

            # Send email
            subject = "Password Reset Request"
            message = f"""
            Hi {user.email},

            You requested a password reset.Below is your One Time Password will expire in 5 minutes:

            {otp}

            If you did not request this, please ignore this email.

            Best regards,
            Agrisarthi Team
            """
            send_email(subject, message, user.email)

            return Response({'message': 'Password reset link has been sent to your email.'}, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    
class PasswordResetAPIView(APIView):
    permission_classes = [AllowAny]
    def put(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')
        otp=request.data.get('otp')
        user_type = request.data.get('user_type')
        if not any(['new_password', 'user_type','otp','email']):
            return Response({'error': 'Email, OTP, and new password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
                try:
                    user = CustomUser.objects.get(email=email,user_type=user_type)
                except CustomUser.DoesNotExist:
                    return Response({'error': 'Invalid user.'}, status=status.HTTP_404_NOT_FOUND)

        # Validate token
                otp_record=EmailOtp.objects.filter(email=email,otp=otp).order_by('-expires_at').first()
                if otp_record is None or otp_record.expires_at < timezone.now():
                    return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)
                user.set_password(new_password)
                user.save()
                subject = "New Password for Agrisarathi Account"
                message = f"""
                Hi {user.name},

                We have successfully reset your password as requested. Below are your new login credentials for your AgriSarthi account:
                
                Email : {email}
                
                New Password : {new_password}

                If you did not request a password reset, please contact our support team immediately at

                Best regards,
                Agrisarthi Team
                """
                send_email(subject, message, user.email)

                return Response({'message': 'Password reset successfully.'}, status=status.HTTP_200_OK)
            


        except Exception as e:
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred during login",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )  
############################--------------------------------Employeer Profiles---------------------------#####################    
class UserProfileView(APIView):
  permission_classes = [IsAuthenticated]
  def get(self, request, format=None):
        user = request.user
        print(f"User is {user.user_type}")
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        print(f"Access token is {provided_access_token}")
        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!="employer":
            return Response({'error': 'User type is not Vednor'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employer=get_object_or_404(Employeer,user=user)
            serializer = EmployerDetailsSerializer(employer)
            return Response({'status': 'success','data':serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e,"An error occured while fetching user profile")
        
  def put(self, request, format=None):
      user = request.user
      print(f"User is {user.user_type}")
      provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
      print(f"Access token is {provided_access_token}")
      if user.access_token != provided_access_token:
          return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
      if user.user_type!="employer":
          return Response({'error': 'User type is not Vednor'}, status=status.HTTP_400_BAD_REQUEST)
      try:
          employer=get_object_or_404(Employeer,user=user)
          serializer = EmployerDetailsSerializer(employer, data=request.data, partial=True)
          if serializer.is_valid():
              serializer.save()
              return Response({'status': 'success','message':'Profile updated successfully'}, status=status.HTTP_200_OK)
          else:
              return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
      except Exception as e:
         return handle_exception(e,"An error occured while updating user profile")
     
     
###################------------------------------Add Employees By Employeer---------------
class AddEmployeeByEmployerView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user = request.user
        print(f"User is {user.user_type}")
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        print(f"Access token is {provided_access_token}")
        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!="employer":
            return Response({'error': 'User type is not Employer'}, status=status.HTTP_400_BAD_REQUEST)
        employee_id = request.data.get("employee_id")
        try:
            employer=get_object_or_404(Employeer,user=user)
            associated_employee = AssociatedEmployees.objects.filter(employeer=employer, employee_id=employee_id).first()
            if associated_employee:
                return Response({'error': 'Employee is already associated with this employer.'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = AddEmployeeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(employeer=employer)
                return Response({'status': 'success','message':'Employee added successfully'}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e,"An error occured while adding employee")
    def get(self, request, format=None):
        user = request.user

        if user.user_type != "employer":
            return Response({'error': 'User is not an employer'}, status=status.HTTP_403_FORBIDDEN)
        try:
            employer = get_object_or_404(Employeer, user=user)
            employees = AssociatedEmployees.objects.filter(employeer=employer)

            serializer = AddEmployeeSerializer(employees, many=True)
            return Response({'status': 'success', 'employees': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e, "An error occurred while fetching employees")
    
    def put(self, request, employee_id, format=None):
        """Update an employee's details partially."""
        user = request.user
        if user.user_type != "employer":
            return Response({'error': 'User is not an employer'}, status=status.HTTP_403_FORBIDDEN)
        try:
            employer = get_object_or_404(Employeer, user=user)
            employee = get_object_or_404(AssociatedEmployees, employeer=employer, employee_id=employee_id)

            serializer = AddEmployeeSerializer(employee, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'message': 'Employee details updated successfully'}, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e, "An error occurred while updating employee details")