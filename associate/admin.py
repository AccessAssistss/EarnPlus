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
    list_display = ('slot', 'day_weeks', 'created_at', 'last_updated_at')
    search_fields = ('slot', 'day_weeks')
    list_filter = ('day_weeks',)
    ordering = ('-created_at',)

# AddExpertBookingSlots Admin
@admin.register(AddExpertBookingSlots)
class AddExpertBookingSlotsAdmin(admin.ModelAdmin):
    list_display = ('expert', 'slot', 'created_at', 'last_updated_at')
    search_fields = ('expert__name', 'slot__slot')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
