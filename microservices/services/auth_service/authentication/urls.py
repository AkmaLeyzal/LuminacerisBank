# auth_service/authentication/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', views.RefreshTokenView.as_view(), name='refresh-token'),
    path('sessions/', views.get_active_sessions, name='active-sessions'),
    path('sessions/<uuid:session_id>/terminate/', 
         views.terminate_session, name='terminate-session'),
    path('profile/', views.get_user_profile, name='user-profile'),
    path('profile/update/', views.update_user_profile, name='update-profile'),
]