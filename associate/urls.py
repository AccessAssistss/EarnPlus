from django.urls import path
from .views import *
urlpatterns = [
    path('AssociateRegistration',AssociateRegistration.as_view(),name='AssociateRegistration'),
    path('AssociateLogin', Associate.as_view(), name='AssociateLogin'),
    ]