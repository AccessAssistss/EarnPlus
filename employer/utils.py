from .models import *
def store_emailotp(identifier,otp):
    try:
        expires_at = timezone.now() + timedelta(minutes=5)
        is_email = re.match(r"[^@]+@[^@]+\.[^@]+", identifier)
        if is_email:
            otp_record, created =EmailOtp.objects.update_or_create(
                email=identifier,
                defaults={
                    'otp': otp,
                    'expires_at': expires_at
                }
            )
        return otp_record
    except Exception as e:
        print(f"Error generating OTP: {str(e)}")
        return None