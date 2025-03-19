from django.db import models
from gigworkers.managers import *
from .choices import *

#################-----------------------Customer Associate-------------------####################
class Associate(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=100,null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=128)
    fcm_token = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=10, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    is_partnership = models.BooleanField(default=False)

################-------------------Customer Associate Booking Slots-------------------------############
class BookingSlots(models.Model):
    slot = models.CharField(max_length=200, choices=slot_choices)
    day_weeks=models.CharField(max_length=200, choices=day_choices,default="Monday")
    created_at = models.DateField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)

###############--------------------------Associate Add Expert Slots--------------------------###############
class AddExpertBookingSlots(models.Model):
    expert = models.ForeignKey(Associate, on_delete=models.CASCADE, null=True, blank=True)
    slot = models.ForeignKey(BookingSlots, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)
