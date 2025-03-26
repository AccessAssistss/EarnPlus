from django.urls import path
from .views import *
urlpatterns = [
    path('AssociateRegistration',AssociateRegistration.as_view(),name='AssociateRegistration'),
    path('AssociateLogin', AssociateLogin.as_view(), name='AssociateLogin'),
    path('HomeScreenAPI',HomeScreenAPI.as_view(), name='HomeScreenAPI'),
    path('GetallSlots',GetallSlots.as_view(), name='GetallSlots'),
    path('AddEmployerByAssociate',AddEmployerByAssociate.as_view(), name='AddEmployerByAssociate'),
    path('AddSlotbyAssociate',AddSlotbyAssociate.as_view(), name='AddSlotbyAssociate'),
    path('GetEKYCBookings',GetEKYCBookings.as_view(), name='GetEKYCBookings'),
    ]