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
from django.db import transaction
import random
from django.contrib.auth.hashers import check_password,make_password
from gigworkers.managers import *
from django.shortcuts import get_object_or_404
from gigworkers.models import *
from .models import *
from .serializers import *
from django.db.models import Q
import pandas as pd
import csv

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
        try:
            employer=get_object_or_404(Employeer,user=user)
            serializer = AddEmployeeSerializer(data=request.data)
            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save(employeer=employer)
                return Response({'status': 'success','message':'Employee added successfully'}, status=status.HTTP_200_OK)
            
            error_messages = []
            for field, errors in serializer.errors.items():
                error_messages.extend(errors)

            return Response({"status": "error", "message": " ".join(error_messages)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e,"An error occured while adding employee")
    def get(self, request, format=None):
        user = request.user

        if user.user_type != "employer":
            return Response({'error': 'User is not an employer'}, status=status.HTTP_403_FORBIDDEN)
        try:
            employer = get_object_or_404(Employeer, user=user)
            employees = GigEmployee.objects.filter(employeer=employer)

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
            employee = get_object_or_404(GigEmployee, employeer=employer, employee_id=employee_id)

            serializer = AddEmployeeSerializer(employee, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success', 'message': 'Employee details updated successfully'}, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e, "An error occurred while updating employee details")
        

########################------------------------Add Employee Data Bulk
class BulkEmployeeAdd(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user = request.user
        print(f"User is {user.user_type}")
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        print(f"Access token is {provided_access_token}")
        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!="employer":
            return Response({'error': 'User type is not Employer'}, status=status.HTTP_400_BAD_REQUEST)
        file=request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employer=Employeer(user=user)
            df = pd.read_excel(file, engine='openpyxl')
            required_columns=['employee_name', 'employee_id', 'email', 'mobile', 'designation', 'dob', 'department', 'date_joined', 'employment_type', 'payment_cycle', 'address']
            if not all(column in df.columns for column in required_columns):
                return Response({'error': 'File does not contain required columns'}, status=status.HTTP_400_BAD_REQUEST)
            ###---------------Flag Handlers

            successful=0
            failed=0
            failed_entries=[]
            new_employees=[]
            existing_mobiles = set(CustomUser.objects.values_list('mobile', flat=True))
            existing_employee_ids = set(GigEmployee.objects.values_list('employee_id',flat=True))
            for index, row in df.iterrows():
                try:
                    mobile=str(row['mobile'])
                    employee_id=str(row['employee_id'])
                    if mobile in existing_mobiles or employee_id in existing_employee_ids:
                        failed += 1
                        failed_entries.append({"employee_id": employee_id, "mobile": mobile, "error": "Duplicate entry"})
                        continue
                    user = CustomUser.objects.create_user(
                            mobile=mobile,  
                            user_type="gigaff"  
                        )
                    new_employees.append(GigEmployee(
                        user=user,
                        employee_name=row['employee_name'],
                        employee_id=employee_id,
                        email=row.get('email', None),
                        mobile=mobile,
                        designation=row['designation'],
                        dob=row['dob'],
                        department=row['department'],
                        date_joined=row['date_joined'],
                        employment_type=row['employment_type'],
                        payment_cycle=row['payment_cycle'],
                        address=row.get('address', None),
                        employeer=employer
                    ))

                    successful += 1
                
                except Exception as e:
                    failed += 1
                    failed_entries.append({"employee_id": row['employee_id'], "mobile": row['mobile'], "error": str(e)})

            #-----------Bulk insert new employees
            if new_employees:
                GigEmployee.objects.bulk_create(new_employees, batch_size=1000)  # Efficient bulk insert
            return Response({
                "status": "success",
                "message": f"{successful} employees added successfully, {failed} failed",
                "failed_entries": failed_entries
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e,"An error occurred while bulk adding employees")

##################################3-----------------------Add Salary Data by Employeer
class AddSalaryDataByEmployerView(APIView):
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
        if not employee_id:
            return Response({'error': 'Employee ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employer=get_object_or_404(Employeer,user=user)
            gig_employee=get_object_or_404(GigEmployee,employee_id=employee_id)
            SalaryHistory.objects.create(
                employer=employer,
                employee=gig_employee,
                daily_salary=request.data.get("daily_salary"),
                salary_date=request.data.get("salary_date"),
            )
            return Response({'status': 'success','message':'Salary data added successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e,"An error occurred while adding salary data")
        
    def get(self,request,format=None):
        user = request.user

        if user.user_type!= "employer":
            return Response({'error': 'User is not an employer'}, status=status.HTTP_403_FORBIDDEN)
        try:
            employer = get_object_or_404(Employeer, user=user)
            paginator=CurrentNewsPagination()
            salary_data = SalaryHistory.objects.filter(employer=employer)
            paginated_transactions=paginator.paginate_queryset(salary_data,request)
            serializer = EmployeeSalaryHistorySerializer(paginated_transactions, many=True)
            return paginator.get_paginated_response({'status':'success','salary_data': serializer.data})
        except Exception as e:
            return handle_exception(e, "An error occurred while fetching salary data")
        