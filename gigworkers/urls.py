from django.urls import path
from .views import *
urlpatterns = [
    path('UserSendOTP',UserSendOTP.as_view(),name='UserSendOTP'),
    path('VerifyOTP', VerifyOTP.as_view(), name='VerifyOTP'),
    path('EmployeesList',EmployeesList.as_view(), name='EmployeesList'),
    path('EmployeeTokenRefreshView',EmployeeTokenRefreshView.as_view(), name='EmployeeTokenRefreshView'),
    path('EmployeeVerification',EmployeeVerification.as_view(), name='EmployeeVerification'),
    path('GetEwaCheckeer',GetEwaCheckeer.as_view(), name='GetEwaCheckeer'),
    path('GetEwaBalance',GetEwaBalance.as_view(),name='GetEwaBalance'),
    ]