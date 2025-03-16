from django.db import models
from gigworkers.managers import *
from datetime import timedelta
from django.utils import timezone
#------------------------------EMPLOYERR MODELS
class Employeer(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=100,null=True, blank=True)
    company_profile=models.FileField(upload_to='employer/profile',null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=128)
    fcm_token = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=10, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    is_partnership = models.BooleanField(default=False)


######################---------------------------Email OTP Models---------------####################
class EmailOtp(models.Model):
    email = models.EmailField(max_length=255, null=True, blank=True)
    mobile = models.CharField(null=True, blank=True, max_length=10, validators=[validate_mobile_no], unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at



