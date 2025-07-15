from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('adminusers/', views.admin_users, name='admin_users'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('verify-login/', views.verify_login, name='verify_login'),
    path('verify-email-profile/', views.verify_email_profile, name='verify_email_profile'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
