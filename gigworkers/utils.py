from rest_framework.views import APIView
from rest_framework.response import Response
from firebase_admin import messaging
from rest_framework.permissions import AllowAny
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
import uuid
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import traceback
import os
from rest_framework import status
from datetime import timedelta
from rest_framework.pagination import LimitOffsetPagination
from .models import *
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
load_dotenv()
import logging
logger = logging.getLogger('gig_app')

#####-------------------------For Creating Refresh and Acces Token
def create_gig_token(user, user_type):
    refresh = RefreshToken.for_user(user)
    refresh['user_type'] = user_type
    
    new_access_token = str(refresh.access_token)
    new_expiry = timezone.now() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
    
    print(f"Creating new token for user {user.id}")
    print(f"Old access token: {user.access_token}")
    print(f"New access token: {new_access_token}")
    
    user.access_token = new_access_token
    user.token_expires_at = new_expiry
    user.save()
    user.refresh_from_db()
    print(f"Saved access token: {user.access_token}")
    
    return {
        'refresh': str(refresh),
        'access': new_access_token,
    }

###############-----------------------Error Handler----------------------###################
def handle_exception(e, message="An unexpected error occurred"):
    error_message = str(e)
    trace = traceback.format_exc()
    print(f"Error: {error_message}")
    return Response({
        "status": "error",
        "message": message,
        "error_message": error_message,
        "traceback": trace
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#################---------------------For Sending Otps
def create_session_with_retries() -> requests.Session:
    """Create a session with retry strategy"""
    session = requests.Session()
    retries = Retry(
        total=3,  # number of retries
        backoff_factor=0.5,  # wait 0.5, 1, 2 seconds between retries
        status_forcelist=[408, 429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
def sendmobile_otp(mobile: str, otp: str) -> bool:
    """
    Send OTP via SMS with improved error handling and retry logic
    
    Args:
        mobile: Mobile number to send OTP to
        otp: The OTP to send
        
    Returns:
        bool: True if successful, False otherwise
    """
    
    url = "http://enterprise.smsgupshup.com/GatewayAPI/rest"
    params = {
        "method": "SendMessage",
        "send_to": mobile,
        "msg": f"{otp} is OTP to Login on Agrisarathi.",
        "msg_type": "TEXT",
        "userid": "2000246092",
        "auth_scheme": "plain",
        "password": "SaPGLOKKG",
        "v": "1.1",
        "format": "text"
    }
    
    session = create_session_with_retries()
    
    try:
        logger.info(f"Attempting to send OTP to {mobile}")
        response = session.post(url, params=params, timeout=(5, 15))  
        
        response.raise_for_status() 
        
        logger.info("OTP sent successfully!")
        logger.debug(f"Response: {response.text}")
        return True
        
    except requests.exceptions.ConnectTimeout:
        logger.error("Connection timed out while trying to send OTP")
        return False
        
    except requests.exceptions.ReadTimeout:
        logger.error("Read timeout while waiting for response")
        return False
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        logger.error(f"Response status code: {e.response.status_code}")
        logger.error(f"Response text: {e.response.text}")
        return False
        
    except requests.exceptions.RequestException as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False
        
    finally:
        session.close()

#################3---------------------------------Store OTP Response--------------------------------#################
def store_otp(identifier, otp):
    expires_at = timezone.now() + timedelta(minutes=5)
    identifier = str(identifier).strip()
    
    if isinstance(identifier, str):
        is_email = re.match(r"[^@]+@[^@]+\.[^@]+", identifier)
        is_mobile = re.match(r"^(?:\+?\d{1,2}\s?)?(?:\d{10,15})$", identifier) 
    else:
        is_email = False
        is_mobile = isinstance(identifier, int) and 1000000000 <= identifier <= 9999999999
    
    if is_email:
        otp_record, created = OTPVerification.objects.update_or_create(
            email=identifier,
            defaults={
                'otp': otp,
                'expires_at': expires_at
            }
        )
    elif is_mobile:
        otp_record, created = OTPVerification.objects.update_or_create(
            mobile=identifier,
            defaults={
                'otp': otp,
                'expires_at': expires_at
            }
        )
    else:
        raise ValueError("Invalid identifier. Must be a valid email or mobile number.")
    return otp_record


########################----------------------------Email Sender
def send_email(subject, message, recipient_list):
    from_email="reachus@agrisarathi.com"
    try:
        message=Mail(
            subject=subject,
            plain_text_content=message,
            from_email=from_email,
            to_emails=[recipient_list],
        )
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        
        
##################----------------------Serializers---------------------------########
class CurrentNewsPagination(LimitOffsetPagination):
    default_limit = 20 
    max_limit = 100  


################################--------------------------------Adhar Send OTP
CASHFREE_CLIENT_ID = "your_client_id"
CASHFREE_CLIENT_SECRET = "your_client_secret"
BASE_URL = "https://sandbox.cashfree.com"
def send_aadhaar_otp(aadhaar_number):
    """
    Calls Cashfree API to send OTP to the Aadhaar-linked mobile number.
    """
    url = f"{BASE_URL}/verification/offline-aadhaar/otp"
    headers = {
        "x-client-id": CASHFREE_CLIENT_ID,
        "x-client-secret": CASHFREE_CLIENT_SECRET,
        "Content-Type": "application/json"
    }
    payload = {"aadhaar_number": aadhaar_number}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data.get("status") == "SUCCESS":
            return {
                "success": True,
                "status": response_data.get("status"),
                "message": response_data.get("message"),
                "ref_id": response_data.get("ref_id")
            }
        else:
            return {
                "success": False,
                "error": response_data.get("message", "Failed to send OTP"),
                "status_code": response.status_code
            }

    except Exception as e:
        return {"success": False, "error": str(e), "status_code": 500}
    
###################################3---------------------AADHAR VERIFY OTP
def verify_aadhaar_otp(otp, ref_id):
    """
    Verifies the Aadhaar OTP using Cashfree API.
    """
    url = f"{BASE_URL}/verification/offline-aadhaar/verify"
    headers = {
        "x-client-id": CASHFREE_CLIENT_ID,
        "x-client-secret": CASHFREE_CLIENT_SECRET,
        "Content-Type": "application/json"
    }
    payload = {
        "otp": otp,
        "ref_id": ref_id
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data.get("status") == "VALID":
            return {
                "success": True,
                "ref_id": response_data.get("ref_id"),
                "status": response_data.get("status"),
                "message": response_data.get("message")
            }
        else:
            return {
                "success": False,
                "error": response_data.get("message", "Aadhaar verification failed"),
                "status_code": response.status_code
            }

    except Exception as e:
        return {"success": False, "error": str(e), "status_code": 500}
    

########################---------------------------Verfiy PAn
def verify_pan(pan,name):
    """
    Verifies the PAN details using Cashfree API.
    """
    url = f"{BASE_URL}/verification/pan"
    headers = {
        "x-client-id": CASHFREE_CLIENT_ID,
        "x-client-secret": CASHFREE_CLIENT_SECRET,
        "Content-Type": "application/json"
    }
    payload = {
        "pan": pan,
        "name": name
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and response_data.get("valid"):
            return {
                "success": True,
                "pan": response_data.get("pan"),
                "type": response_data.get("type"),
                "reference_id": response_data.get("reference_id"),
                "name_provided": response_data.get("name_provided"),
                "registered_name": response_data.get("registered_name"),
                "message": response_data.get("message"),
                "pan_status": response_data.get("pan_status")
            }
        else:
            return {
                "success": False,
                "error": response_data.get("message", "PAN verification failed"),
                "status_code": response.status_code
            }

    except Exception as e:
        return {"success": False, "error": str(e), "status_code": 500}
    
#################################-----------------------------Check PAn Status
def check_pan_status(reference_id):
    """
    Checks the status of PAN verification using reference_id (GET Request).
    """
    url = f"{BASE_URL}/verification/pan/{reference_id}"
    headers = {
        "x-client-id": CASHFREE_CLIENT_ID,
        "x-client-secret": CASHFREE_CLIENT_SECRET
    }

    try:
        response = requests.get(url, headers=headers)
        response_data = response.json()

        if response.status_code == 200:
            return {
                "success": True,
                "status": response_data.get("pan_status"),
                "message": response_data.get("message"),
                "valid": response_data.get("valid")
            }
        else:
            return {
                "success": False,
                "error": response_data.get("message", "PAN status check failed"),
                "status_code": response.status_code
            }
    except Exception as e:
        return {"success": False, "error": str(e), "status_code": 500}
    

######################-----------------------------gNERATE unique id
def generate_verification_id():
    """Generates a valid verification ID (max 50 chars, allowed chars: a-zA-Z0-9.-_)"""
    raw_id = str(uuid.uuid4())[:50]
    return re.sub(r"[^a-zA-Z0-9._-]", "", raw_id)