from django.shortcuts import render
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
import random
from .managers import *
from django.shortcuts import get_object_or_404
from .models import *
from django.db import transaction
from django.conf import settings
from .utils import *
from .serializers import *
import razorpay
from employer.models import *
# Create your views here.
TEST_MOBILE = 1239956739
STATIC_OTP = 612743

class UserSendOTP(APIView):
    permission_classes = [AllowAny]
    def post(self, request, format=None):
        user_type = request.data.get('user_type','gigaff')
        mobile = request.data.get('mobile')
        if mobile == TEST_MOBILE:
            otp = STATIC_OTP
            print(f"Test user login: Mobile {mobile}, using static OTP {otp}")
        else:
            otp = random.randint(100000, 999999)
            print(f"Generated OTP: {otp}")

        try:
                user = CustomUser.objects.filter(mobile=mobile, user_type=user_type).first()
                is_existing_user = GigEmployee.objects.filter(user=user).exists() if user else False
                if user:
                    sendmobile_otp(mobile, otp)
                    store_otp(mobile, otp)
                    return Response({
                        'message': f"OTP sent successfully to {user.mobile}",
                        'otp': otp,
                        'is_existing_user': is_existing_user
                    }, status=status.HTTP_200_OK)
                else:
                    sendmobile_otp(mobile, otp)
                    store_otp(mobile, otp)
                    return Response({
                        'message': f"OTP sent successfully to {mobile}",
                        'otp': otp,
                        'is_existing_user': False
                    }, status=status.HTTP_200_OK)

        except Exception as e:
            return handle_exception(e,"An error occurred while Sending OTP")

#################------------------------------------------Verify Otp-------------------###############
class VerifyOTP(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        try:
            mobile = request.data.get("mobile")
            otp = request.data.get("otp")
            user_type = request.data.get("user_type")

            if not mobile or not otp or not user_type:
                return Response({"error": "Mobile number, OTP, and user type are required"}, status=status.HTTP_400_BAD_REQUEST)

            if mobile == TEST_MOBILE and otp == STATIC_OTP:
                user, created = CustomUser.objects.get_or_create(mobile=TEST_MOBILE, defaults={"user_type": user_type})
                is_existing_user = GigEmployee.objects.filter(user=user).exists()
                return Response({
                    "message": "Test user OTP verified successfully", 
                    "is_existing_user": is_existing_user
                }, status=status.HTTP_200_OK)

            otp_record = OTPVerification.objects.filter(otp=otp, mobile=mobile).order_by("-expires_at").first()
            if not otp_record or otp_record.expires_at < timezone.now():
                return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

            otp_record.delete()

            user = CustomUser.objects.filter(mobile=mobile, user_type=user_type).first()
            is_existing_user = GigEmployee.objects.filter(user=user).exists()

            # Check if the user has visited the employer screen
            is_screen_visited = GigEmployee.objects.filter(user=user).first()
            screen_check = is_screen_visited.is_employer_screen if is_screen_visited else False

            ######------------------Check if the user is part of an employer
            associated_employee = AssociatedEmployees.objects.filter(phone_number=mobile).first()
            is_employer_part = False
            if associated_employee:
                is_employer_part = GigEmployee.objects.filter(associated_employeer=associated_employee.employeer, mobile=mobile).exists()

            if user and is_existing_user:
                tokens = create_gig_token(user, user_type)
                return Response({
                    "message": "OTP verified successfully.",
                    "is_existing_user": True,
                    "screen_check": screen_check,
                    "is_employer_part": is_employer_part,
                    "tokens": tokens
                }, status=status.HTTP_200_OK)

            if not user:
                serializer = EmployeeRegistrationSerializer(data={"mobile": mobile, "user_type": user_type})
                if serializer.is_valid():
                    user = serializer.save()
                    tokens = create_gig_token(user, user_type)
                    return Response({
                        "message": "OTP verified successfully. User registered.",
                        "is_existing_user": False,
                        "screen_check": screen_check,
                        "is_employer_part": is_employer_part,
                        "tokens": tokens
                    }, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            else:
                tokens = create_gig_token(user, user_type)
                return Response({
                    "message": "OTP verified successfully.",
                    "is_existing_user": is_existing_user,
                    "is_employer_part": is_employer_part,
                    "screen_check": screen_check,
                    "tokens": tokens
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return handle_exception(e, "An error occurred while verifying OTP")

###################3---------------------------------Employee LOGIN
class EmployeerLinkCheck(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user = request.user
        print(f"User is :{user}")
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]

        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type!= "gigaff":
            return Response({'error': 'Only Giugs can view Request'}, status=status.HTTP_403_FORBIDDEN)
        employee_id=request.data.get('employee_id')
        if not employee_id:
            return Response({'error': 'Employee ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employee=get_object_or_404(GigEmployee,user=user)
            if employee.employee_id == employee_id or employee.mobile==employee_id:
                employee.is_employer_screen = True
                employee.save()
                return Response({'message': 'Success: Employer link verified'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Mismatch: Provided employee ID does not match with Selected employer'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e,"An error occurred while checking employer link")
         
        
###############-------------------------List ALL Employeers------------------
class EmployeesList(APIView):
    permission_classes = [AllowAny]
    def get(self,request,format=None):
        search=request.query_params.get("search")
        try:
            employer=Employeer.objects.filter(is_deleted=False)
            if search:
                employer=employer.filter(name__icontains=search)
            serializers=EmployeerListSerializer(employer,many=True)
            return Response({'status':'success','data':serializers.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e,"An error occurred while listing employers")

###########################-------------------------Adhaar vERFCIATION AND sTRATUS uPDATES----------------------############
class AdhaarOTPSent(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        """
        Accepts Aadhaar number from user and sends OTP using Cashfree API.
        """
        aadhaar_number = request.data.get("aadhaar_number")

        if not aadhaar_number:
            return Response({"error": "Aadhaar number is required"}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]

        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type!= "gigaff":
            return Response({'error': 'Only Giugs can view Request'}, status=status.HTTP_403_FORBIDDEN)
        try:
            employee=get_object_or_404(GigEmployee,user=user)
            verification, created = EmployeeVerification.objects.get_or_create(employee=employee,aadhar_number=aadhaar_number)
            otp_response = send_aadhaar_otp(aadhaar_number)

            if otp_response["success"]:
                return Response({
                    "status": otp_response["status"],
                    "message": otp_response["message"],
                    "ref_id": otp_response["ref_id"]
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": otp_response["error"]}, status=otp_response["status_code"])

        except Exception as e:
           return handle_exception(e,"An error occured while sending OTP")
####################################------------------------------AADHAR OTP VERIFIVCATIONS
class AdhaarOTPVerification(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        """
        Accepts Aadhaar number & OTP to vERIDY DETAILS.
        """
        ref_id = request.data.get("ref_id")
        otp=request.data.get("otp")
        if not ref_id or not otp:
            return Response({"error": "Referebce ID & OTP is required"}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]

        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type!= "gigaff":
            return Response({'error': 'Only Giugs can view Request'}, status=status.HTTP_403_FORBIDDEN)
        try:
            employee=get_object_or_404(GigEmployee,user=user)
            verifcation=get_object_or_404(EmployeeVerification,employe=employee)
            verification_response = verify_aadhaar_otp(otp,ref_id)
            if verification_response["success"]:
                verifcation.aadhar_verified=True
                verifcation.save()
                return Response({
                "ref_id": verification_response["ref_id"],
                "status": verification_response["status"],
                "message": verification_response["message"]
            }, status=status.HTTP_200_OK)
            else:
                return Response({"error": verification_response["error"]}, status=verification_response["status_code"])
        except Exception as e:
            return handle_exception(e,"An error occurred while verifying OTP")

#################-----------------------------------------------PAN VERFICATION AND GET STATUS-------------------------################################
class VerifyPan(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        """
        Accepts User Name and PAN NO AS INPUT.
        """
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]

        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type!= "gigaff":
            return Response({'error': 'Only Giugs can view Request'}, status=status.HTTP_403_FORBIDDEN)
        name = request.data.get("name")
        pan=request.data.get("pan")
        if not name or not pan:
            return Response({"error": "Name and Pan is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employee=get_object_or_404(GigEmployee,user=user)
            verifcation=get_object_or_404(EmployeeVerification,employe=employee)
            verification_response = verify_pan(pan, name)
            if verification_response["success"]:
                verifcation.pan_number=pan
                verifcation.save()
                return Response({
                    "pan": verification_response["pan"],
                    "type": verification_response["type"],
                    "reference_id": verification_response["reference_id"],
                    "name_provided": verification_response["name_provided"],
                    "registered_name": verification_response["registered_name"],
                    "message": verification_response["message"],
                    "pan_status": verification_response["pan_status"]
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": verification_response["error"]}, status=verification_response["status_code"])
        except Exception as e:
            return handle_exception(e,"An error occurred while verifying PAN")
        
    def get(self, request):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type!= "gigaff":
            return Response({'error': 'Only Giugs can view Request'}, status=status.HTTP_403_FORBIDDEN)
        reference_id=request.query_params.get('reference_id')
        if not reference_id:
            return Response({"error": "Reference ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employee=get_object_or_404(GigEmployee,user=user)
            verification=get_object_or_404(EmployeeVerification,employe=employee)
            status_response = check_pan_status(reference_id)
            if status_response["success"]:
                verification.pan_verified=True
                verification.save()
                return Response(status_response, status=status.HTTP_200_OK)
            else:
                return Response({"error": status_response["error"]}, status=status_response["status_code"])
        except Exception as e:
            return handle_exception(e,"An error occurred while checking PAN status")
#####################################3-------------------FACE LIVELESSNESS---------------------------------
class FaceLivelinessAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type!= "gigaff":
            return Response({'error': 'Only Giugs can view Request'}, status=status.HTTP_403_FORBIDDEN)
        image = request.FILES.get("image")
        verification_id = request.data.get("verification_id")

        if not image:
            return Response({"error": "Image is required"}, status=status.HTTP_400_BAD_REQUEST)
        employee=get_object_or_404(GigEmployee,user=user)
        verification =get_object_or_404(EmployeeVerification,employee=employee)
        verification.selfie=image
        verification.save()
        if not verification_id:
            verification_id = generate_verification_id()

        # Prepare request for Cashfree API
        url = f"{BASE_URL}/verification/liveliness"
        headers = {
            "x-client-id": CASHFREE_CLIENT_ID,
            "x-client-secret": CASHFREE_CLIENT_SECRET
        }
        files = {"image": verification.selfie.open("rb")}
        data = {
            "verification_id": verification_id,
            "strict_check": "true"
        }
        try:
            response = requests.post(url, headers=headers, files=files, data=data)
            response_data = response.json()

            if response.status_code == 200:

                return Response({
                    "success": True,
                    "message": "Liveliness verification completed",
                    "reference_id": response_data.get("reference_id"),
                    "verification_id": verification_id,
                    "status": response_data.get("status"),
                    "liveliness": response_data.get("liveliness"),
                    "score": response_data.get("score")
                }, status=status.HTTP_200_OK)

            return Response({"error": response_data.get("message", "Liveliness verification failed")}, 
                            status=response.status_code)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
###################-------------------------------Video Kyc 
class VideoKyc(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        """
        Accepts User Name and PAN NO AS INPUT.
        """
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]

        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type!= "gigaff":
            return Response({'error': 'Only Giugs can view Request'}, status=status.HTTP_403_FORBIDDEN)
        file=request.FILES.get('file')
        if not file:
            return Response({"error": "File is required"}, status=status.HTTP_400_BAD_REQUEST)  
        try:
            employee=get_object_or_404(GigEmployee,user=user)
            verification=get_object_or_404(EmployeeVerification,employe=employee)
            verification.video_kyc=file
            verification.save()
            return Response({"message": "Video KYC uploaded successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e,"An error occurred while uploading video KYC")
############################-------------------------------User ProfiLE View
class UserProfileView(APIView):
  permission_classes = [IsAuthenticated]
  def get(self, request, format=None):
        user = request.user
        print(f"User is {user.user_type}")
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        print(f"Access token is {provided_access_token}")
        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!="gigaff":
            return Response({'error': 'User type is not Gig'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employee=get_object_or_404(GigEmployee,user=user)
            serializer = SalariedEmployeesSerializer(employee)
            return Response({'status': 'success','data':serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e,"An error occured while fetching user profile")
        

####################################3--------------------------SETUP FEESS SUBSCRIPTIONS----------------------------#######################
#1.BuySubscription
razorpay_client = razorpay.Client(auth=(os.environ.get('RAZORPAY_API_KEY'),os.environ.get('RAZORPAY_API_SECRET')))    
class BuyFranchiseSubscription(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]

        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!="gigaff":
            return Response({'error': 'User type is not Gigs'}, status=status.HTTP_400_BAD_REQUEST)
        amount = float(request.data.get('amount', 0))
        discount = float(request.data.get('discount', 0))
        if not amount:
            return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee=get_object_or_404(GigEmployee,user=user)
            with transaction.atomic():
                subscription = FranchiseSubscribed(
                        employee=employee,
                        amount=amount,
                        discount=discount
                    )

                subscription.calculate_total_amount()
                subscription.save()
                print(f"Subscription is :{subscription}")

                    #-------------Razorpay order creation
                razorpay_order = razorpay_client.order.create({
                    "amount": int(subscription.total_amount * 100), 
                    "currency": "INR",
                    "receipt": subscription.subscription_id,
                    "payment_capture": 1
                    })

                subscription.razorpay_order_id = razorpay_order['id']
                subscription.save()

                return Response({
                    "subscription_id": subscription.subscription_id,
                    "razorpay_order_id": razorpay_order['id'],
                    "amount": subscription.total_amount,
                    "currency": "INR",
                }, status=status.HTTP_200_OK)

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
        
#######----------------Franchise Payment Success
class FranchisePaymentSuccess(APIView):
    permission_classes = [IsAuthenticated]
    async def post(self, request, format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]

        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=401)
        if user.user_type!="gigaff":
            return Response({'error': 'User type is not Gigs'}, status=400)
        try:
            employee=get_object_or_404(GigEmployee,user=user)
            razorpay_payment_id = request.data.get('razorpay_payment_id')
            razorpay_order_id = request.data.get('razorpay_order_id')
            razorpay_signature = request.data.get('razorpay_signature')

            if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
                return Response({'error': 'All payment fields are required'}, status=400)
            try:
                razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
                })
            except razorpay.errors.SignatureVerificationError:
                return Response({'error': 'Payment signature verification failed'}, status=400)

            with transaction.atomic():
                subscription = get_object_or_404(FranchiseSubscribed, razorpay_order_id=razorpay_order_id)
                subscription.payment_status = "success"
                subscription.razorpay_payment_id=razorpay_payment_id
                subscription.razorpay_signature_id=razorpay_signature
                    # ----------------------Send Email notifications
                email_subject = 'Subscription Payment Successful'
                email_message_fpo = f"""
                Dear {subscription.employee.name},

                Your subscription (ID: {subscription.subscription_id}) has been successfully processed.
                """
                send_email(email_subject, email_message_fpo, [subscription.employee.email])

                    # -----------------Send SMS notifications
                #sms_message_fpo = f"Dear {subscription.fpo.fpo_name}, your subscription has been processed."
                #send_sms(subscription.fpo.mobile, sms_message_fpo)

                # ----------------- Store Real-Time Notifications in Database
                # Send notification to FPO
                OrderNotifications.objects.create(
                        employee=employee,
                        notification_type="franchise",
                        message=f"Your subscription (ID: {subscription.subscription_id}) has been successfully processed."
                    )
                employee.buy_franchise=True
                subscription.save()
                    
                return Response({"status": "success", "message": "Payment successful"}, status=status.HTTP_200_OK)

        except Exception as e:
            subscription.payment_status = "failed"
            error_message = str(e)
            trace = traceback.format_exc()
            return Response(
                {
                    "status": "error",
                    "message": "An unexpected error occurred",
                    "error_message": error_message,
                    "traceback": trace
                },
                status=500
            )

##################-----------------------------Add Bank infor by Gig Employee------------------##########
class EmployeeBankInfo(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]

        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type!= "gigaff":
            return Response({'error': 'Only Giugs can view Request'}, status=status.HTTP_403_FORBIDDEN)
        try:
            employee=get_object_or_404(GigEmployee,user=user)
            serializer=AddGigBankeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(associated_employeer=employee.associated_employees)
                return Response({"message": "Bank details added successfully."}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e,"An error occurred while Adding Bank Details")
        
    def put(self,request,format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!= "gigaff":
            return Response({'error': 'Only Giugs can view Request'}, status=status.HTTP_403_FORBIDDEN)
        try:
            employee=get_object_or_404(GigEmployee,user=user)
            serializer=AddGigBankeSerializer(data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Bank details updated successfully."}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e,"An error occurred while Updating Bank Details")
        

####################---------------------------------Add Employability and Personal Detaisl BY NON PARTNERSHIP-----------------#######
class AddEmployeeByEmployerView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, format=None):
        user = request.user
        print(f"User is {user.user_type}")
        provided_access_token = request.META.get('HTTP_AUTHORIZATION').split(' ')[1]
        print(f"Access token is {provided_access_token}")
        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!="gigaff":
            return Response({'error': 'User type is not Employer'}, status=status.HTTP_400_BAD_REQUEST)
        employee_id = request.data.get('employee_id')
        try:
            non_salaried=get_object_or_404(GigEmployee,user=user)
            associated_employee = GigEmployee.objects.filter(employee_id=employee_id,associated_employees__isnull=True,assocated_employeer__isnull=True).first()
            if associated_employee:
                return Response({'error': 'Employee ID is already associated with this employer.'}, status=status.HTTP_400_BAD_REQUEST)
            serializer = AddnonEmployeeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'success','message':'Employee added successfully'}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e,"An error occured while adding employee")
        
    def get(self, request, format=None):
        user = request.user

        if user.user_type != "gigaff":
            return Response({'error': 'User is not an employer'}, status=status.HTTP_403_FORBIDDEN)
        try:
            non_salaried=get_object_or_404(GigEmployee,user=user)
            employees = GigEmployee.objects.filter(associated_employees__isnull=True,assocated_employeer__isnull=True)
            serializer = AddnonEmployeeSerializer(employees, many=True)
            return Response({'status': 'success', 'employees': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e,"An error occurred while listing employees")


        
    
 
################--------------------------Refersh Token-------------------####################
class EmployeeTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            access_token = response.data.get("access")
            refresh_token = request.data.get("refresh")
            try:
                refresh_token_obj = RefreshToken(refresh_token)
                user_id = refresh_token_obj["user_id"]
                print(f"User ID: {user_id}")

                user = CustomUser.objects.get(id=user_id)
                print(f"User is: {user}")
                if user.id == user_id:  
                    user.access_token = access_token
                    user.token_expires_at = timezone.now() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] 
                    user.save()
                else:
                    return Response({"error": "Invalid user"}, status=status.HTTP_403_FORBIDDEN)

            except CustomUser.DoesNotExist:
                return Response({"error": "Farmer not found"}, status=status.HTTP_404_NOT_FOUND)

        return response
    
########------------------------------Get Ewa Checkeer of User
class GetEwaCheckeer(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.user_type!= "gigaff":
            return Response({'error': 'Only Giugs can view Request'}, status=status.HTTP_403_FORBIDDEN)
        try:
            employee=get_object_or_404(GigEmployee,user=user)
            is_eligible = employee.is_eligible_for_ewa()
            if not is_eligible:
                return Response({'error': 'You are not eligible for Earned Wage Access (EWA).'}, status=status.HTTP_403_FORBIDDEN)
            return Response({'message':'success', 'checkeer':is_eligible},status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e,"An error occurred while fetching EWA checkeer")
    

#################----------------------Get EWA Balance-------------------#################
class CheckEWABalance(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]

        if user.access_token!= provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type!= "gigaff":
            return Response({'error': 'Only Giugs can view Request'}, status=status.HTTP_403_FORBIDDEN)
        try:
            employee=get_object_or_404(GigEmployee,user=user,is_affilated=True)
            salary_details = SalaryDetails.objects.filter(employee=employee).first()
            if not salary_details:
                return Response({"error": "Employee is not active or has no salary details"}, status=status.HTTP_404_NOT_FOUND)
            earned_wages = salary_details.calculate_earned_wages()
            return Response({'message':'success', 'salary_details':earned_wages},status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e,"An error occurred while fetching EWA balance")
        
######################-------------------------Request EWA Balance by Employee
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
class RequestEWA(APIView):
    permission_classes = [IsAuthenticated]
    @transaction.atomic
    def post(self, request, format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type != "gigaff":
            return Response({'error': 'Only gig employees can request EWA.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            employee = get_object_or_404(GigEmployee, user=user)
            if not employee.is_eligible_for_ewa():
                return Response({'error': 'You are not eligible for Earned Wage Access (EWA).'}, status=status.HTTP_403_FORBIDDEN)

            salary_details = SalaryDetails.objects.filter(employee=employee).first()
            if not salary_details:
                return Response({"error": "Employee is not active or has no salary details."}, status=status.HTTP_404_NOT_FOUND)

            salary_details.calculate_earned_wages()
            requested_amount = Decimal(request.data.get('amount'))
            if requested_amount > salary_details.ewa_limit:
                return Response({"error": "Requested amount exceeds EWA limit."}, status=status.HTTP_400_BAD_REQUEST)

            salary_details.update_ewa_limit_after_withdrawal(requested_amount)
            #-------Create EWA transaction
            ewa_transaction = EWATransaction.objects.create(
                employee=employee,
                amount=requested_amount,
                due_date=salary_details.calculate_due_date()
            )
            bank_detail=get_object_or_404(BankDetails,employee=employee)
            ewa_transaction.calculate_interest()

            #-------------Initiate Razorpay payout
            payout_response = razorpay_client.payout.create({
                "account_number": bank_detail.account_number,  
                "fund_account_id": employee.razorpay_fund_account_id,  
                "amount": int(requested_amount * 100), 
                "currency": "INR",
                "mode": "IMPS",
                "purpose": "salary",
                "queue_if_low_balance": True,
                "reference_id": str(ewa_transaction.transaction_id),
            })

            #----------------Check if payout was successful
            if payout_response.get('id'):
                ewa_transaction.razorpay_payment_id = payout_response['id']
                ewa_transaction.status = 'COMPLETED'
                ewa_transaction.save()
                return Response({
                    'message': 'EWA request initiated and amount credited.',
                    'transaction_id': ewa_transaction.transaction_id,
                    'amount': requested_amount,
                    'ewa_limit_remaining': salary_details.ewa_limit,
                }, status=status.HTTP_200_OK)
            else:
                # If payout fails, raise an exception to trigger a rollback
                raise Exception("Failed to initiate payout.")

        except Exception as e:
            return handle_exception(e,"An error occcured while making payouts")
    def get(self,request,format=None):
        user = request.user
        provided_access_token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[-1]
        if user.access_token != provided_access_token:
            return Response({'error': 'Access token is invalid or has been replaced.'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.user_type != "gigaff":
            return Response({'error': 'Only gig employees can request EWA.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            employee = get_object_or_404(GigEmployee, user=user)
            ewa_transactions = EWATransaction.objects.filter(employee=employee).order_by('-withdrawal_date')
            paginator=CurrentNewsPagination()
            paginated_transactions=paginator.paginate_queryset(ewa_transactions,request)
            serializer = EWATransactionSerializer(paginated_transactions, many=True)
            return Response({'status':"sucees","data": serializer.data},status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e,"An error occurred while fetching EWA Transactions details")