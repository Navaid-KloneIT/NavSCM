from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/invite/', views.user_invite_view, name='user_invite'),
    path('profile/', views.profile_view, name='profile'),
]
