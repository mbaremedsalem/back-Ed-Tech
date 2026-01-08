# """
# users/views.py
# """

# from rest_framework import generics, permissions, status
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework_simplejwt.tokens import RefreshToken
# from django.contrib.auth import login, logout
# from .models import User
# from .serializers import (
#     UserSerializer, RegisterSerializer, LoginSerializer,
#     TeacherProfileSerializer, StudentProfileSerializer
# )

# class RegisterView(generics.CreateAPIView):
#     serializer_class = RegisterSerializer
#     permission_classes = [permissions.AllowAny]
    
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.save()
        
#         # إنشاء ملف تعريف بناءً على الدور
#         if user.role == 'teacher':
#             TeacherProfile.objects.create(user=user)
#         elif user.role == 'student':
#             StudentProfile.objects.create(user=user)
        
#         refresh = RefreshToken.for_user(user)
        
#         return Response({
#             'user': UserSerializer(user).data,
#             'refresh': str(refresh),
#             'access': str(refresh.access_token),
#         }, status=status.HTTP_201_CREATED)

# class LoginView(APIView):
#     permission_classes = [permissions.AllowAny]
    
#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data['user']
        
#         login(request, user)
#         refresh = RefreshToken.for_user(user)
        
#         # تحديد رابط إعادة التوجيه بناءً على الدور
#         redirect_url = self.get_redirect_url(user)
        
#         return Response({
#             'user': UserSerializer(user).data,
#             'refresh': str(refresh),
#             'access': str(refresh.access_token),
#             'redirect_url': redirect_url
#         })
    
#     def get_redirect_url(self, user):
#         if user.role == 'admin':
#             return '/admin/'
#         elif user.role == 'teacher':
#             return '/teacher/dashboard/'
#         elif user.role == 'student':
#             return '/student/learn/'
#         return '/'

# class LogoutView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
    
#     def post(self, request):
#         logout(request)
#         return Response({'message': 'تم تسجيل الخروج بنجاح'})

# class UserProfileView(generics.RetrieveUpdateAPIView):
#     serializer_class = UserSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_object(self):
#         return self.request.user

# class TeacherProfileView(generics.RetrieveUpdateAPIView):
#     serializer_class = TeacherProfileSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_object(self):
#         return self.request.user.teacher_profile

# class StudentProfileView(generics.RetrieveUpdateAPIView):
#     serializer_class = StudentProfileSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_object(self):
#         return self.request.user.student_profile

# class RoleBasedView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get(self, request):
#         user = request.user
#         data = {
#             'role': user.role,
#             'permissions': self.get_permissions(user),
#             'dashboard_url': self.get_dashboard_url(user)
#         }
#         return Response(data)
    
#     def get_permissions(self, user):
#         # إرجاع الصلاحيات بناءً على الدور
#         if user.role == 'admin':
#             return ['manage_users', 'manage_content', 'view_analytics', 'system_settings']
#         elif user.role == 'teacher':
#             return ['create_content', 'view_students', 'view_reports', 'manage_class']
#         elif user.role == 'student':
#             return ['access_content', 'submit_activities', 'view_progress']
#         return []
    
#     def get_dashboard_url(self, user):
#         if user.role == 'admin':
#             return '/admin/dashboard/'
#         elif user.role == 'teacher':
#             return '/teacher/dashboard/'
#         elif user.role == 'student':
#             return '/student/dashboard/'
#         return '/'




"""
users/views.py - الإصدار المصحح
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from .models import User, TeacherProfile, StudentProfile  # ← استيراد هنا
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    TeacherProfileSerializer, StudentProfileSerializer
)

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # إنشاء ملف تعريف بناءً على الدور
        if user.role == 'teacher':
            TeacherProfile.objects.create(user=user)
        elif user.role == 'student':
            StudentProfile.objects.create(user=user)  # ← الآن معرف
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        login(request, user)
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        logout(request)
        return Response({'message': 'تم تسجيل الخروج بنجاح'})

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class TeacherProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user.teacher_profile

class StudentProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user.student_profile

class RoleBasedView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        data = {
            'role': user.role,
            'permissions': self.get_permissions(user),
        }
        return Response(data)
    
    def get_permissions(self, user):
        # إرجاع الصلاحيات بناءً على الدور
        if user.role == 'admin':
            return ['manage_users', 'manage_content', 'view_analytics', 'system_settings']
        elif user.role == 'teacher':
            return ['create_content', 'view_students', 'view_reports', 'manage_class']
        elif user.role == 'student':
            return ['access_content', 'submit_activities', 'view_progress']
        return []