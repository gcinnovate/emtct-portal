# from django.conf.urls import url, include
from django.urls import path, re_path
import emtct.views as emtct_views
# from .views import MotherRegistration, region_list, district_list, subcounty_list, parish_list
from django.contrib.auth import views as auth_views
# from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings
from django.contrib.auth.views import (PasswordResetView, PasswordResetDoneView, PasswordChangeView,
                                       PasswordChangeDoneView, PasswordResetConfirmView, PasswordResetCompleteView )

urlpatterns = [

    
    # path('', auth_views.login, name='login', kwargs={'redirect_authenticated_user': True,
    #                                                     'template_name': 'emtct/login.html',
    #                                                     'redirect_field_name': 'send-verification'

    #                                                   }),
    path('', auth_views.LoginView.as_view(redirect_authenticated_user= True,
                                                template_name= 'emtct/login.html',
                                                redirect_field_name='send-verification') , name='login'),

    path('logout/',  auth_views.LogoutView.as_view(next_page= settings.LOGOUT_REDIRECT_URL), name='logout'),
    # path('logout/',auth_views.logout , {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'), #

    path('submit-verification/', emtct_views.submit_verification, name='submit-code'),
    path('send-verification/', emtct_views.send_verification_code, name='send-code'),
    path('register-user/', emtct_views.register_user, name='register-user'),
    re_path(r'^user/(?P<pk>[0-9]+)', emtct_views.UserUpdate.as_view(), name='user-update'),
    path('users/', emtct_views.UserList.as_view(), name='users-list'),
    re_path(r'^users/(?P<pk>[0-9]+)', emtct_views.UserDetail.as_view, name='user-detail'),
    path('help/', emtct_views.Help.as_view(), name='help'),
    path('overview/', emtct_views.Overview.as_view(), name='overview'),
    path('add-rapidpro/', emtct_views.create_rapidpro, name='create-rapidpro'),
    path('mother_registration/', emtct_views.MotherRegistration.as_view(), name='mother_registration'), #mother_registration
    path('emtct-data-export/', emtct_views.generate_emtct_export, name='generate-emtct-export'),
    path('emtct-data-import/', emtct_views.import_ugandaemr_emtct_export, name='uganda-emtct-import'),
    path('password-change/',
        PasswordChangeView.as_view(template_name='emtct/password_change_form.html'),
        name='password_change'),
    path('password-change/done/',
        PasswordChangeDoneView.as_view(template_name='emtct/password_change_done.html'),
        name='password_change_done'),

    path('password-reset/',
        PasswordResetView.as_view(template_name='emtct/password_reset_form.html'),
        name='password_reset'),
    path('password-reset/done/',
        PasswordResetDoneView.as_view(template_name='emtct/password_reset_done.html'),
        name='password_reset_done'),
    path('reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/',
        PasswordResetConfirmView.as_view(template_name='emtct/password_reset_confirm.html'),
        name='password_reset_confirm'),
    path('reset/done/',
        PasswordResetCompleteView.as_view(template_name='emtct/password_reset_complete.html'),
        name='password_reset_complete'),
    path('regionjson/', emtct_views.region_list, name= 'region_list'),
    path('mother_registration/districtjson/<int:id>', emtct_views.district_list, name= 'district_list'),
    path('mother_registration/subcountyjson/<int:id>', emtct_views.subcounty_list, name= 'subcounty_list'),
    path('mother_registration/parishjson/<int:id>', emtct_views.parish_list, name= 'parish_list'),

        


    ]

