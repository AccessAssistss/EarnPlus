from django.contrib import admin
from .models import *
# Associate Admin
@admin.register(Associate)
class AssociateAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'mobile', 'is_deleted', 'is_partnership', 'created', 'updated_at')
    search_fields = ('name', 'email', 'mobile')
    list_filter = ('is_deleted', 'is_partnership')
    ordering = ('-created',)

# BookingSlots Admin
@admin.register(BookingSlots)
class BookingSlotsAdmin(admin.ModelAdmin):
    list_display = ('slot', 'created_at')
    search_fields = ('slot',)
    list_filter = ('slot',)
    ordering = ('-created_at',)


#################-------------------Associate Booking Slots Admin--------------------------################
@admin.register(AddAssoicateBookingSlots)
class AddAssoicateBookingSlotsAdmin(admin.ModelAdmin):
    list_display = ('associate', 'slot', 'created_at', 'updated_at', 'is_deleted')
    list_filter = ('associate', 'is_deleted')
    search_fields = ('associate__name', 'slot__slot')
    list_editable = ('is_deleted',)
    ordering = ('-created_at',)


#################-------------------Book KYC Slot with Employee Admin--------------------------################
@admin.register(BookkycEmployee)
class BookkycEmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee', 'associate', 'slot', 'created_at', 'updated_at', 'is_deleted')
    list_filter = ('associate', 'employee', 'is_deleted')
    search_fields = ('employee__employee_name', 'associate__name', 'slot__slot__slot')
    list_editable = ('is_deleted',)
    ordering = ('-created_at',)