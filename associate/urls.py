from django.urls import path
from .views import *
urlpatterns = [
    path('AssociateRegistration',AssociateRegistration.as_view(),name='AssociateRegistration'),
    path('AssociateLogin', AssociateLogin.as_view(), name='AssociateLogin'),
    path('HomeScreenAPI',HomeScreenAPI.as_view(), name='HomeScreenAPI'),
    ]