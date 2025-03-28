from django.shortcuts import render
from gigworkers.utils import *
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
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
from .utils import *
from associate.models import *
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
                return Response({'error': 'User with this mobile number or Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
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
    authentication_classes = [JWTAuthentication]
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
  authentication_classes = [JWTAuthentication]
  permission_classes = [IsAuthenticated]
  throttle_classes = [UserRateThrottle]
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
            serializer = EmployerFinalViewSerializer(employer)
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
     
###########################-------------------------Update EMPLOYEE additional details
class UpdateEmployeeDetailsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        
        if user.access_token != provided_access_token:
            return Response(
                {'error': 'Access token is invalid or has been replaced.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if user.user_type != "employer":
            return Response({'error': 'User type is not Employer'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employer = get_object_or_404(Employeer, user=user)
            response_data = {}

            # ------------------------- Update business details if provided
            business_fields = [
                'business_location', 'business_type', 'business_description','total_employees',
                'established_date', 'registration_number', 'gst_number',
                'pincode', 'country_id', 'state_id', 'district_id'
            ]
            business_data = {key: request.data[key] for key in request.data if key in business_fields}

            if business_data:
                business_details, created = EmployerBusinessDetails.objects.get_or_create(employer=employer)
                serializer = EmployerBusinessesDetailsSerializer(business_details, data=business_data, partial=True)
                if serializer.is_valid():
                    business_details = serializer.save()
                    response_data['business_details'] = serializer.data
                else:
                    return Response(
                        {'error': 'Invalid business details data', 'details': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # ------------------------- Update company policies if provided
            policy_fields = [
                'notice_period_days', 'probation_period_days', 'total_annual_leaves',
                'sick_leaves', 'casual_leaves', 'maternity_leaves', 'working_hours_per_day',
                'overtime_policy', 'resignation_policy', 'remote_work_policy', 'other_policies'
            ]
            policy_data = {key: request.data[key] for key in request.data if key in policy_fields}

            if policy_data:
                company_policies, created = EmployerCompanyPolicies.objects.get_or_create(employer=employer)
                serializer = EmployerCompanyPoliciesSerializer(company_policies, data=policy_data, partial=True)
                if serializer.is_valid():
                    company_policies = serializer.save()
                    response_data['company_policies'] = serializer.data
                else:
                    return Response(
                        {'error': 'Invalid company policies data', 'details': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )

           
            # ------------------------- No valid data provided
            if not response_data:
                return Response(
                    {'error': 'No valid data provided for update'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {'message': 'Employer details updated successfully', 'data': response_data},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'error': 'An error occurred while updating data', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
#####################-----------------------Addd Email & Work Locations--------------------#####
class AddEmailContractWorkLocation(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if user.access_token != provided_access_token:
            return Response(
                {"error": "Access token is invalid or has been replaced."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if user.user_type != "employer":
            return Response(
                {"error": "User type is not Employer"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        filter_type=request.data.get("filter_type")
        if not filter_type:
            return Response({"error": "Filter type must be provided."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employer=get_object_or_404(Employeer,user=user)
            if filter_type=="email":
                email=request.data.get('email')
                email_type=request.data.get('email_type')
                if not email or not email_type:
                    return Response({"error": "Email and Email Type must be provided."}, status=status.HTTP_400_BAD_REQUEST)
                existing_data=EmployerEmailsDetails.objects.filter(email=email,employer=employer,email_type=email_type).exists()
                if existing_data:
                    return Response({"error": "Email already exists for selected type."}, status=status.HTTP_400_BAD_REQUEST)
                EmployerEmailsDetails.objects.create(employer=employer,email=email,email_type=email_type)
                return Response({"status":"success","message": "Email Data added successfully."}, status=status.HTTP_200_OK)
            elif filter_type=="payment_cycle":
                payment_cycle=request.data.get('payment_cycle')
                contract_type_id=request.data.get('contract_type_id')
                if not payment_cycle or not contract_type_id:
                    return Response({"error": "Payment Cycle & Contract Type must be provided."}, status=status.HTTP_400_BAD_REQUEST)
                existing_data=EmployerPaymentCycle.objects.filter(payment_cycle=payment_cycle,employer=employer,
                                                                  contract_type_id=contract_type_id).exists()
                if existing_data:
                    return Response({"error": "Payment Cycle already exists for selected type."}, status=status.HTTP_400_BAD_REQUEST)
                EmployerPaymentCycle.objects.create(employer=employer,payment_cycle=payment_cycle,contract_type_id=contract_type_id)
                return Response({"status":"success","message": "Payment Cycle successfully added."}, status=status.HTTP_200_OK)
            elif filter_type=="contract":
                contract_under=request.data.get('contract_under',[])
                if not contract_under:
                    return Response({"error": "Contract Under must be provided."}, status=status.HTTP_400_BAD_REQUEST)
                existing_data=EmployerrTypeContract.objects.filter(
                    employer=employer,
                    contract_under__in=contract_under
                ).exists()
                if existing_data:
                    return Response({"error": "Contract already exists for selected types."}, status=status.HTTP_400_BAD_REQUEST)
                for contract_type_id in contract_under:
                    EmployerrTypeContract.objects.get_or_create(
                        employer=employer,
                        contract_under_id=contract_type_id
                    )
                return Response({"status":"success","message": "Contract successfully added."}, status=status.HTTP_200_OK)
            elif filter_type=="location":
                state_id=request.data.get('state_id')
                country_id=request.data.get('country_id')
                district_id=request.data.get('district_id')
                work_location_name=request.data.get('work_location_name')
                total_employees=request.data.get('total_employees')
                if not state_id or not country_id or not district_id or not work_location_name or not total_employees:
                    return Response({"error": "State, Country, District, Work Location Name and Total Employees must be provided."}, status=status.HTTP_400_BAD_REQUEST)
                existing_data=EmployerWorkLocation.objects.filter(
                    employer=employer,
                    country_id=country_id,
                    state_id=state_id,
                    district_id=district_id,
                    work_location_name=work_location_name
                ).exists()
                if existing_data:
                    return Response({"error": "Work Location already exists for selected state, country and district."}, status=status.HTTP_400_BAD_REQUEST)
                EmployerWorkLocation.objects.create(
                    employer=employer,
                    country_id=country_id,
                    state_id=state_id,
                    district_id=district_id,
                    work_location_name=work_location_name,
                    total_employees=total_employees)
                return Response({"status":"success","message": "Work Location added successfully."}, status=status.HTTP_200_OK)
                
        except Exception as e:
            return handle_exception(e,"An error  occured while posting data")
    def put(self,request,format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if user.access_token != provided_access_token:
            return Response(
                {"error": "Access token is invalid or has been replaced."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if user.user_type != "employer":
            return Response(
                {"error": "User type is not Employer"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        filter_type=request.data.get("filter_type")
        if not filter_type:
            return Response({"error": "Filter type must be provided."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employer=get_object_or_404(Employeer,user=user)
            if filter_type=="email":
                email=request.data.get('email',None)
                email_type=request.data.get('email_type',)
                if not email or not email_type:
                    return Response({"error": "Email and Email Type must be provided."}, status=status.HTTP_400_BAD_REQUEST)
                data=get_object_or_404(EmployerEmailsDetails,employer=employer)
                data.email=email
                data.email_type=email_type
                data.save()
                return Response({"status":"success","message": "Email Data Updated successfully."}, status=status.HTTP_200_OK)
            elif filter_type=="location":
                state_id=request.data.get('state_id')
                country_id=request.data.get('country_id')
                district_id=request.data.get('district_id')
                work_location_name=request.data.get('work_location_name')
                total_employees=request.data.get('total_employees')
                if not state_id or not country_id or not district_id or not work_location_name or not total_employees:
                    return Response({"error": "State, Country, District, Work Location Name and Total Employees must be provided."}, status=status.HTTP_400_BAD_REQUEST)
                data=get_object_or_404(EmployerWorkLocation,employer=employer)
                data.country_id=country_id
                data.state_id=state_id
                data.district_id=district_id
                data.work_location_name=work_location_name
                data.total_employees=total_employees
                data.save()
                return Response({"status":"success","message": "Work Location added successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e,"An error  occured while posting data")
    def delete(self,request,format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        if user.access_token != provided_access_token:
            return Response(
                {"error": "Access token is invalid or has been replaced."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if user.user_type != "employer":
            return Response(
                {"error": "User type is not Employer"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        filter_type=request.data.get("filter_type")
        if not filter_type:
            return Response({"error": "Filter type must be provided."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employer=get_object_or_404(Employeer,user=user)
            if filter_type=="email":
                email_ids=request.data.get("email_ids",[])
                data=EmployerEmailsDetails.objects.filter(employer=employer,id__in=email_ids)
                data.delete()
                return Response({"status":"success","message": "Email Data deleted successfully."}, status=status.HTTP_200_OK)
            elif filter_type=="location":
                location_id=request.data.get("location_id",[])
                if not location_id:
                    return Response({"error": "Location ID must be provided."}, status=status.HTTP_400_BAD_REQUEST)
                data=EmployerWorkLocation.objects.filter(id__in=location_id,employer=employer)
                data.delete()
                return Response({"status":"success","message": "Work Location deleted successfully."}, status=status.HTTP_200_OK)
            elif filter_type=="contract":
                contract_id=request.data.get("contract_id",[])
                if not contract_id:
                    return Response({"error": "Contract ID must be provided."}, status=status.HTTP_400_BAD_REQUEST)
                data=EmployerrTypeContract.objects.filter(employer=employer,id__in=contract_id)
                data.delete()
                return Response({"status":"success","message": "Contract deleted successfully."}, status=status.HTTP_200_OK)
            elif filter_type=="payment_cycle":
                payment_cycle_id=request.data.get("payment_cycle_id",[])
                if not payment_cycle_id:
                    return Response({"error": "Payment Cycle ID must be provided."}, status=status.HTTP_400_BAD_REQUEST)
                data=EmployerPaymentCycle.objects.filter(employer=employer,id__in=payment_cycle_id)
                data.delete()
                return Response({"status":"success","message": "Payment Cycle deleted successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid filter type provided."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e,"An error  occured while deleting data")
#######################----------------------Add Contract Select by Employer-----------########
class AddgetContractbyEmployer(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request,format=None):
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
            contracts=ContractTypes.objects.all()
            data=ContractTypesSerializer(contracts,many=True)
            return Response({'status':'success','data':data.data}, status=status.HTTP_200_OK) 
        except Exception as e:
            return handle_exception(e,"An error occured while fetching contract")
###################------------------------------Add Employees By Employeer---------------
class AddEmployeeByEmployerView(APIView):
    authentication_classes = [JWTAuthentication]
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
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        print(f"Access token is {provided_access_token}")
        if user.user_type != "employer":
            return Response({'error': 'User is not an employer'}, status=status.HTTP_403_FORBIDDEN)
        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            employer = get_object_or_404(Employeer, user=user)
            paginator=CurrentNewsPagination()
            employees = GigEmployee.objects.filter(employeer=employer)
            paginated_transactions=paginator.paginate_queryset(employees,request)
            serializer = AddEmployeeSerializer(paginated_transactions, many=True)
            return paginator.get_paginated_response({'status':'success','data': serializer.data})
        except Exception as e:
            return handle_exception(e, "An error occurred while fetching employees")
        
    def delete(sef,request,format=None):
        """Delete an employee by their employee ID."""
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        print(f"Access token is {provided_access_token}")
        if user.user_type != "employer":
            return Response({'error': 'User is not an employer'}, status=status.HTTP_403_FORBIDDEN)
        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        employee_id = request.data.get('employee_id')
        if not employee_id:
            return Response({'error': 'Employee ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employer = get_object_or_404(Employeer, user=user)
            employee = get_object_or_404(GigEmployee, employeer=employer, employee_id=employee_id)
            employee.delete()
            return Response({'status':'success','message':'Employee deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e, "An error occurred while deleting employee")
    
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        print(f"User is {user.user_type}")
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        print(f"Access token is {provided_access_token}")
        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type != "employer":
            return Response({'error': 'User type is not Employer'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get employer instance linked to the user
            employer = get_object_or_404(Employeer, user=user)

            df = pd.read_excel(file, engine='openpyxl')
            required_columns = ['employee_name', 'employee_id', 'email', 'mobile', 'designation', 'dob', 'department', 'date_joined', 'employment_type', 'payment_cycle', 'address','gender','marital_status']

            if not all(column in df.columns for column in required_columns):
                return Response({'error': 'File does not contain required columns'}, status=status.HTTP_400_BAD_REQUEST)

            successful = 0
            failed = 0
            failed_entries = []
            new_employees = []

            existing_mobiles = set(CustomUser.objects.values_list('mobile', flat=True))
            existing_employee_ids = set(GigEmployee.objects.values_list('employee_id', flat=True))

            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        mobile = str(row['mobile'])
                        employee_id = str(row['employee_id'])

                        #--------------Check for duplicates
                        if mobile in existing_mobiles or employee_id in existing_employee_ids:
                            failed += 1
                            failed_entries.append({"employee_id": employee_id, "mobile": mobile, "error": "Duplicate entry"})
                            continue

                        user = CustomUser.objects.create_user(
                            mobile=mobile,
                            user_type="gigaff"
                        )

                        #---------------Create new GigEmployee instance
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

                #----------Bulk insert new employees
                if new_employees:
                    GigEmployee.objects.bulk_create(new_employees, batch_size=1000)  # Efficient bulk insert

            return Response({
                "status": "success",
                "message": f"{successful} employees added successfully, {failed} failed",
                "failed_entries": failed_entries
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return handle_exception(e, "An error occurred while bulk adding employees")

##################################3-----------------------Add Salary Data by Employeer
class AddSalaryDataByEmployerView(APIView):
    authentication_classes = [JWTAuthentication]
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
        
############################------------------------Addd Rating BY Employeer--------------------#############
class AddRatingByEmployeer(APIView):
    authentication_classes = [JWTAuthentication]
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
        employee_id = request.data.get('employee_id')
        rating=request.data.get('rating',5)
        description=request.data.get('description',None)
        if not ([employee_id,rating]):
            return Response({'error': 'All required fields are missing'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employer=get_object_or_404(Employeer,user=user)
            employee=get_object_or_404(GigEmployee,employee_id=employee_id)
            rating_obj=RateEmployee.objects.filter(employer=employer,employee=employee).first()
            if rating_obj:
                return Response({'error': 'You have already rated this employee.'}, status=status.HTTP_400_BAD_REQUEST)
            rating_obj=RateEmployee.objects.create(employer=employer,employee=employee,rating=rating,description=description)
            rating_obj.save()
            return Response({"message": "Rating added successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e, "An error occurred while adding rating")
        
    def get(self,request,format=None):
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
            data=RateEmployee.objects.filter(is_deleted=False)
            paginator=CurrentNewsPagination()
            paginated_transactions=paginator.paginate_queryset(data,request)
            serializer = EmployeeRatingSerializer(paginated_transactions, many=True)
            return paginator.get_paginated_response({'status':'success','rating_data': serializer.data})
        except Exception as e:
            return handle_exception(e, "An error occurred while fetching ratings")
    def delete(self,request,format=None):
        user = request.user
        print(f"User is {user.user_type}")
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        print(f"Access token is {provided_access_token}")
        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!="employer":
            return Response({'error': 'User type is not Employer'}, status=status.HTTP_400_BAD_REQUEST)
        rating_id=request.data.get('rating_id')
        if not rating_id:
            return Response({'error': 'Rating ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employer=get_object_or_404(Employeer,user=user)
            rating=get_object_or_404(RateEmployee,id=rating_id,employer=employer)
            rating.delete()
            return Response({"message": "Rating deleted successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e, "An error occurred while deleting rating")
        
        
###################-----------------------Employee Active and Inactive ---------------#########
class GetHomeScreenKPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request,format=None):
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
            active_employees=GigEmployee.objects.filter(employeer=employer,is_affilated=True).count()
            inactive_employees=GigEmployee.objects.filter(employeer=employer,is_affilated=False).count()
            return Response({"status":"success","active_employees": active_employees,"inactive_employees": inactive_employees}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e, "An error occurred while fetching employer details")
    