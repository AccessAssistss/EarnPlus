from django.urls import path
from .views import *

urlpatterns = [
    path('EmployerRegistration',EmployerRegistration.as_view(),name='EmployerRegistration'),
    path('EmployerLogin', EmployerLogin.as_view(), name='EmployerLogin'),
    path('FCMTokenView',FCMTokenView.as_view(), name='FCMTokenView'),
    path('TockenChecker',TockenChecker.as_view(), name='TockenChecker'),
    path('PasswordResetRequestAPIView',PasswordResetRequestAPIView.as_view(), name='PasswordResetRequestAPIView'),
    path('PasswordResetAPIView',PasswordResetAPIView.as_view(), name='PasswordResetAPIView'),
    path('UserProfileView',UserProfileView.as_view(),name='UserProfileView'),
    path('UpdateEmployeeDetailsView',UpdateEmployeeDetailsView.as_view(),name='UpdateEmployeeDetailsView'),
    path('BulkEmployeeAdd',BulkEmployeeAdd.as_view(),name='BulkEmployeeAdd'),
    path('AddEmployeeByEmployerView',AddEmployeeByEmployerView.as_view(),name='AddEmployeeByEmployerView'),
    path('AddEmployeeByEmployerView/<str:employee_id>',AddEmployeeByEmployerView.as_view(),name='AddEmployeeByEmployerView'),
    path('AddgetContractbyEmployer',AddgetContractbyEmployer.as_view(),name='AddgetContractbyEmployer'),
    path('AddEmailContractWorkLocation',AddEmailContractWorkLocation.as_view(),name='AddEmailContractWorkLocation'),
    path('GetHomeScreenKPI',GetHomeScreenKPI.as_view(),name='GetHomeScreenKPI'),
    ]