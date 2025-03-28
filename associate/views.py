from rest_framework_simplejwt.authentication import JWTAuthentication
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
from employer.serializers import *
from employer.models import *
from django.db.models import Q
import pandas as pd
import csv

# Create your views here.
###############---------------Authorization
##----------1.User Registration
class AssociateRegistration(APIView):
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
            serializer = AssociateRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e,"An error occured while registration")
            
####################-------------------------------------REST API's Login----------------###############
class AssociateLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = AssociateLoginSerializer(data=request.data)
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
        
######################----------------------Add Employer By Assocaite----------------###########
class AddEmployerByAssociate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user = request.user
        print(f"User is {user.user_type}")
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        print(f"Access token is {provided_access_token}")
        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type != "associate":
            return Response({'error': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)
        user_type = request.data.get('user_type')
        mobile = request.data.get('mobile')
        email = request.data.get('email')
        name = request.data.get('name')
        ip_address = request.META.get('REMOTE_ADDR')
        print(f"Registration attempt with mobile: {mobile}, user_type: {user_type}, IP address: {ip_address}")
        try:
            associate=get_object_or_404(Associate,user=user)
            user = CustomUser.objects.filter(
            Q(email=email, user_type=user_type) | Q(mobile=mobile, user_type=user_type)
            ).exists()
            print(f"User is :{user}")
            if user:
                return Response({'error': 'User with this mobile number or Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = AssociateEmployerRegistrationSerializer(data=request.data,context={'request': request})
            if serializer.is_valid():
                user = serializer.save()
                email_message = generate_registration_email(user)
                send_email("Welcome to Earn+", email_message,email)
                return Response({'status':'success','message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e,"An error occured while registration")
        
    def get(self,request,format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!= "associate":
            return Response({'error': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            associate=get_object_or_404(Associate,user=user)
            paginator=CurrentNewsPagination()
            employers = Employeer.objects.filter(associate=associate)
            paginated_transactions=paginator.paginate_queryset(employers ,request)
            serializer = AssociatedEmployers(paginated_transactions, many=True)
            return paginator.get_paginated_response({'status':'success','data': serializer.data})
        except Exception as e:
            return handle_exception(e,"An error occurred while fetching employer details")
    
    def delete(self, request, format=None):
        user = request.user
        print(f"User is {user.user_type}")
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        print(f"Access token is {provided_access_token}")
        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type != "associate":
            return Response({'error': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)

        employer_ids = request.data.get('employer_id', [])
        if not employer_ids:
            return Response({'error': 'No employer provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            associate = get_object_or_404(Associate, user=user)
            employers = Employeer.objects.filter(id__in=employer_ids, associate=associate)
            if not employers.exists():
                return Response({'error': 'No matching employer(s) found'}, status=status.HTTP_404_NOT_FOUND)

            users_to_delete = [employer.user for employer in employers if hasattr(employer, 'user')]
            employers.delete()
            for use in users_to_delete:
                use.delete()
            return Response({'status': 'success', 'message': 'Employer(s) deleted successfully'}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return handle_exception(e, "An error occurred while deleting employer")
    
###################-------------------Get Total Employers----------------------###########
class HomeScreenAPI(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!= "associate":
            return Response({'error': 'Only Associate can view Employers'}, status=status.HTTP_403_FORBIDDEN)
        try:
            associate=get_object_or_404(Associate,user=user)
            active_employer=Employeer.objects.filter(is_active=True).count()
            inactive_employer=Employeer.objects.filter(is_active=False).count()
            return Response({"status":"success","active_employers": active_employer,"inactive_employers": inactive_employer}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e, "An error occurred while fetching employer details")
###################----------------Get All Slots By Admin-------------#####
class GetallSlots(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        user = request.user
        if user.user_type!= "associate":
            return Response({'error': 'Only Admin can view slots'}, status=status.HTTP_403_FORBIDDEN)
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            associate=get_object_or_404(Associate,user=user)
            slots=BookingSlots.objects.all()
            data=BookSlotsSerializer(slots,many=True)
            return Response({'status':'success','data': data.data})
        except Exception as e:
            return handle_exception(e, "An error occurred while fetching slots")
            
        
        
        
###################-----------------------------Add KYC Slots By Associates----------------##########
class AddSlotbyAssociate(APIView):
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!= "associate":
            return Response({'error': 'Only Associate can add KYC slots'}, status=status.HTTP_403_FORBIDDEN)
        slots=request.data.get('slots',[])
        if not slots:
            return Response({'error': 'Slot IDs are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            assoicate=get_object_or_404(Associate,user=user)
            added_slots=[]
            skipped_slots=[]
            for i in slots:
                try:
                    booking_slot=get_object_or_404(BookingSlots,id=i)
                except BookingSlots.DoesNotExist:
                     return Response({'error': f'Slot with ID {i} does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
                if AddAssoicateBookingSlots.objects.filter(associate=assoicate,slot=booking_slot).exists():
                    skipped_slots.append(i)
                    continue
                add_slot=AddAssoicateBookingSlots.objects.create(associate=assoicate,slot=booking_slot)
                added_slots.append(add_slot.id)
            return Response({'message': 'Slots added successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return handle_exception(e, "An error occurred while adding slots")
    
    def get(self,request,format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!= "associate":
            return Response({'error': 'Only Associate can view KYC slots'}, status=status.HTTP_403_FORBIDDEN)
        try:
            associate=get_object_or_404(Associate,user=user)
            paginator=CurrentNewsPagination()
            slots=AddAssoicateBookingSlots.objects.filter(associate=associate)
            paginated_transactions=paginator.paginate_queryset(slots ,request)
            serializer=AssociateSlotsSerializer(paginated_transactions,many=True)
            return paginator.get_paginated_response({'status':'success','data': serializer.data})
        except Exception as e:
            return handle_exception(e, "An error occurred while fetching slots")
    
    def delete(self,request,format=None):
        user = request.user
        print(f"User is {user.user_type}")
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        print(f"Access token is {provided_access_token}")
        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type != "associate":
            return Response({'error': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)
        slot=request.data.get('slots')
        if not slot:
            return Response({'error': 'No slot provided'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            associate=get_object_or_404(Associate,user=user)
            add_slot=get_object_or_404(AddAssoicateBookingSlots,associate=associate,id=slot)
            add_slot.delete()
            return Response({'message': 'Slot deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e, "An error occurred while Delketing Slots.") 
            
            
#################------------------------Get KYC Boookings--------------######################
class GetEKYCBookings(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!= "associate":
            return Response({'error': 'Only Associate can view KYC bookings'}, status=status.HTTP_403_FORBIDDEN)
        try:
            associate=get_object_or_404(Associate,user=user)
            paginator=CurrentNewsPagination()
            bookings=BookkycEmployee.objects.filter(associate=associate).order_by('-created_at')
            paginated_transactions=paginator.paginate_queryset(bookings ,request)
            serializer=BookKycSerializer(paginated_transactions,many=True)
            return paginator.get_paginated_response({'status':'success','data': serializer.data})
        except Exception as e:
            return handle_exception(e, "An error occurred while fetching bookings")
        
    def put(self,request,format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!= "associate":
            return Response({'error': 'Only Associate can view KYC bookings'}, status=status.HTTP_403_FORBIDDEN)
        try:
            associate=get_object_or_404(Associate,user=user)
            booking_id=request.data.get('booking_id')
            if not booking_id:
                return Response({'error': 'Booking ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            booking=get_object_or_404(BookkycEmployee,id=booking_id,associate=associate)
            serializer=BookKycSerializer(booking)
            return Response({'status':'success','data': serializer.data})
        except Exception as e:
            return handle_exception(e, "An error occurred while Updating booking details")
        
        
            
