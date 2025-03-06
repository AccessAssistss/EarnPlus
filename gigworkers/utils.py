from rest_framework.views import APIView
from rest_framework.response import Response
from firebase_admin import messaging
from rest_framework.permissions import AllowAny
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
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