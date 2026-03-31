"""
users/urls.py
"""

from django.urls import path
from . import views

urlpatterns = [
    # إنشاء حساب مدير جديد (بدون تسجيل دخول)
    path('admin/register/', views.AdminRegistrationView.as_view(), name='admin-register'),
    
    path('register/', views.RegisterView.as_view(), name='register'),
    path('wilayas/', views.WilayaListView.as_view(), name='wilayas-list'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/teacher/', views.TeacherProfileView.as_view(), name='teacher-profile'),
    path('profile/student/', views.StudentProfileView.as_view(), name='student-profile'),
    path('role-info/', views.RoleBasedView.as_view(), name='role-info'),
    # --------debit -------    
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password', views.ResetPasswordView.as_view(), name='reset_password'),
    path('verify-token/', views.VerifyTokenView.as_view(), name='verify_token'),

    # ------- URLs pour administrateurs -------
    path('admin/students/', views.AdminStudentListView.as_view(), name='admin-students-list'),
    path('admin/teachers/', views.AdminTeacherListView.as_view(), name='admin-teachers-list'),
    path('admin/students/<int:id>/', views.AdminStudentDetailView.as_view(), name='admin-student-detail'),
    path('admin/teachers/<int:id>/', views.AdminTeacherDetailView.as_view(), name='admin-teacher-detail'),
]