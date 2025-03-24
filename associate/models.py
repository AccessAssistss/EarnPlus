from django.db import models
from gigworkers.managers import *
from .choices import *
from gigworkers.models import *

from datetime import datetime

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
    
#########################------------------Contract Types----------------#######
class ContractTypes(models.Model):
    contract_type = models.CharField(max_length=100, choices=[
        ('Type 1', 'Type 1'),
        ('Type 2', 'Type 2'),
        ('Type3', 'Type3'),
        ('All', 'All'),
    ], default='Type1')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

################-------------------Customer Associate Booking Slots-------------------------############
class BookingSlots(models.Model):
    slot = models.CharField(max_length=200, choices=slot_choices)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted=models.BooleanField(default=False)

###############--------------------------Associate Add Expert Slots--------------------------###############
class AddAssoicateBookingSlots(models.Model):
    associate = models.ForeignKey(Associate, on_delete=models.CASCADE, null=True, blank=True)
    slot = models.ForeignKey(BookingSlots, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted=models.BooleanField(default=False)

########################-------------------Book KYC Slot with Employee-----------------##########
class BookkycEmployee(models.Model):
    employee=models.ForeignKey('gigworkers.GigEmployee',on_delete=models.CASCADE, null=True, blank=True)
    associate=models.ForeignKey(Associate,on_delete=models.CASCADE, null=True, blank=True)
    slot=models.ForeignKey(AddAssoicateBookingSlots,on_delete=models.CASCADE, null=True, blank=True)
    slot_date=models.DateField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    meet_link=models.URLField(blank=True,null=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted=models.BooleanField(default=False)
    
    def save(self,*args, **kwargs):
        if self.slot and self.slot_date and not self.meet_link:
            slot_time=self.slot.slot.slot.split(' - ')[0]
            slot__24hr=datetime.strptime(slot_time,"%I:%M %p").strftime("%H:%M")