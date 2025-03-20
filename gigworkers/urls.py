from django.urls import path
from .views import *
urlpatterns = [
    ####---------------------------AUth & Registration
    path('UserSendOTP',UserSendOTP.as_view(),name='UserSendOTP'),
    path('VerifyOTP', VerifyOTP.as_view(), name='VerifyOTP'),
    path('EmployeesList',EmployeesList.as_view(), name='EmployeesList'),
    path('EmployeeTokenRefreshView',EmployeeTokenRefreshView.as_view(), name='EmployeeTokenRefreshView'),
    path('AdhaarOTPSent',AdhaarOTPSent.as_view(), name='AdhaarOTPSent'),
    path('AdhaarOTPVerification',AdhaarOTPVerification.as_view(), name='AdhaarOTPVerification'),
    path('VerifyPan',VerifyPan.as_view(), name='VerifyPan'),
    path('FaceLivelinessAPI',FaceLivelinessAPI.as_view(), name='FaceLivelinessAPI'),
    path('EmployeeBankInfo',EmployeeBankInfo.as_view(), name='EmployeeBankInfo'),
    path('EmployeerLinkCheck',EmployeerLinkCheck.as_view(), name='EmployeerLinkCheck'),
#########################33------------------------------Home Screens------------------------------###########
    path('UserProfileView',UserProfileView.as_view(), name='UserProfileView'),
    path('GetSalaryTracking',GetSalaryTracking.as_view(),name='GetSalaryTracking'),
    path('GetEwaCheckeer',GetEwaCheckeer.as_view(), name='GetEwaCheckeer'),
    path('CheckEWABalance',CheckEWABalance.as_view(),name='CheckEWABalance'),
    path('RequestEWA',RequestEWA.as_view(), name='RequestEWA'),
    ]