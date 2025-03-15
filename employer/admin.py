from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(Employeer)
class EmployeerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'mobile', 'is_partnership', 'is_deleted', 'created')
    search_fields = ('name', 'email', 'mobile')
    list_filter = ('is_partnership', 'is_deleted', 'created')
    ordering = ('-created',)


