"""
users/urls.py
"""

from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/teacher/', views.TeacherProfileView.as_view(), name='teacher-profile'),
    path('profile/student/', views.StudentProfileView.as_view(), name='student-profile'),
    path('role-info/', views.RoleBasedView.as_view(), name='role-info'),
]