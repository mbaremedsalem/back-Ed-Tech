"""
users/views.py - الإصدار المصحح
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout

from utilities.helpers import get_current_host
from .models import User, TeacherProfile, StudentProfile  # ← استيراد هنا
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    TeacherProfileSerializer, StudentProfileSerializer
)

from rest_framework import generics, permissions, parsers

# views.py
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import os
from .models import User
from .serializers import AdminRegisterSerializer, UserSerializer

class AdminRegistrationView(generics.CreateAPIView):
    """
    API لإنشاء حساب مدير جديد بدون الحاجة إلى تسجيل الدخول
    يتطلب كود سري للمصادقة
    """
    serializer_class = AdminRegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        # === الحماية: التحقق من الكود السري ===
        admin_secret_code = request.data.get('admin_secret_code')
        
        # الحصول على الكود السري من إعدادات Django
        expected_secret_code = getattr(settings, 'ADMIN_REGISTRATION_SECRET_CODE', None)
        
        # إذا لم يتم تعريف الكود السري في الإعدادات
        if not expected_secret_code:
            # محاولة الحصول من متغيرات البيئة
            expected_secret_code = os.environ.get('ADMIN_REGISTRATION_SECRET_CODE')
            
        if not expected_secret_code:
            return Response(
                {
                    "detail": "لم يتم تكوين كود التسجيل الإداري",
                    "code": "ADMIN_SECRET_NOT_CONFIGURED"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # التحقق من صحة الكود السري
        if not admin_secret_code or admin_secret_code != expected_secret_code:
            return Response(
                {
                    "detail": "كود التسجيل الإداري غير صالح",
                    "code": "INVALID_ADMIN_SECRET"
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # === الحماية: التحقق من وجود مديرين بالفعل ===
        # (اختياري: لمنع إنشاء مديرين بعد التثبيت الأول)
        if hasattr(settings, 'ALLOW_MULTIPLE_ADMINS') and not settings.ALLOW_MULTIPLE_ADMINS:
            if User.objects.filter(role='admin', is_staff=True).exists():
                return Response(
                    {
                        "detail": "يوجد مدير بالفعل في النظام",
                        "code": "ADMIN_ALREADY_EXISTS"
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # === الحماية: التحقق من الـ IP (اختياري) ===
        allowed_ips = getattr(settings, 'ADMIN_REGISTRATION_ALLOWED_IPS', [])
        if allowed_ips:
            client_ip = request.META.get('REMOTE_ADDR')
            if client_ip not in allowed_ips:
                return Response(
                    {
                        "detail": "عنوان IP غير مصرح به",
                        "code": "IP_NOT_ALLOWED"
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # === معالجة البيانات ===
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # حفظ المستخدم
        user = serializer.save()
        
        # إنشاء توكنات JWT
        refresh = RefreshToken.for_user(user)
        
        # تسجيل الحدث (اختياري)
        import logging
        logger = logging.getLogger('admin_registration')
        logger.info(f"تم إنشاء حساب مدير جديد: {user.username} - IP: {request.META.get('REMOTE_ADDR')}")
        
        return Response({
            "message": "تم إنشاء حساب المدير بنجاح",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .models import TeacherProfile, StudentProfile,Wilaya
from .serializers import RegisterSerializer, UserSerializer,WilayaSerializer

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    
    def get_permissions(self):
        # Seul un admin authentifié peut créer des utilisateurs avec rôle teacher/student
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Récupérer le rôle de l'utilisateur à créer
        user_role = serializer.validated_data.get('role', '')
        
        # Vérifier si l'utilisateur connecté est admin
        # Si non-admin essaie de créer teacher/student, refuser
        if user_role in ['teacher', 'student'] and not request.user.is_staff:
            return Response(
                {"detail": "Vous n'avez pas la permission de créer des enseignants ou étudiants."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = serializer.save()
        
        # Créer le profil approprié
        if user.role == 'teacher':
            TeacherProfile.objects.create(user=user)
        elif user.role == 'student':
            StudentProfile.objects.create(user=user)
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class WilayaListView(generics.ListAPIView):
    """
    Vue pour lister toutes les wilayas
    """
    queryset = Wilaya.objects.all()
    serializer_class = WilayaSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Désactiver la pagination pour avoir toutes les wilayas
    
# class RegisterView(generics.CreateAPIView):
#     serializer_class = RegisterSerializer
    
#     def get_permissions(self):
#         # Seul un admin authentifié peut créer des utilisateurs avec rôle teacher/student
#         if self.request.method == 'POST':
#             return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
#         return [permissions.IsAuthenticated()]

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
        
#         # Récupérer le rôle de l'utilisateur à créer
#         user_role = serializer.validated_data.get('role', '')
        
#         # Vérifier si l'utilisateur connecté est admin
#         # Si non-admin essaie de créer teacher/student, refuser
#         if user_role in ['teacher', 'student'] and not request.user.is_staff:
#             return Response(
#                 {"detail": "Vous n'avez pas la permission de créer des enseignants ou étudiants."},
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         user = serializer.save()
        
#         # Créer le profil approprié
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
# ----- debit ------
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
import string

from .serializers import (
    EmailSerializer, 
    CustomPasswordTokenSerializer,
    ResetPasswordRequestSerializer
)

User = get_user_model()

class ForgotPasswordView(APIView):
    """
    Endpoint pour demander une réinitialisation de mot de passe
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                # Générer un token
                token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                
                # Sauvegarder le token (dans un modèle temporaire ou session)
                # Pour l'exemple, on va stocker dans le modèle User
                user.reset_password_token = token
                user.reset_password_token_created = timezone.now()
                user.save()
                host = get_current_host(request)
                # Envoyer l'email
                reset_link = f"{host}api/auth/reset-password?token={token}&email={email}"
                
                # Email HTML
                subject = "Réinitialisation de votre mot de passe"
                html_message = render_to_string('emails/password_reset.html', {
                    'user': user,
                    'reset_link': reset_link,
                    'token': token,
                })
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                return Response({
                    'message': 'Un email de réinitialisation a été envoyé.',
                    'email': email
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                # Pour la sécurité, ne pas révéler si l'email existe
                return Response({
                    'message': 'Si cet email existe, vous recevrez un lien de réinitialisation.'
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    """
    Endpoint pour réinitialiser le mot de passe avec token
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = CustomPasswordTokenSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            password = serializer.validated_data['password']
            email = serializer.validated_data.get('email')
            
            try:
                if email:
                    user = User.objects.get(email=email, reset_password_token=token)
                else:
                    # Chercher par token seulement
                    user = User.objects.get(reset_password_token=token)
                
                # Vérifier si le token n'a pas expiré (24h)
                token_age = timezone.now() - user.reset_password_token_created
                if token_age > timedelta(hours=24):
                    return Response({
                        'error': 'Le token a expiré.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Mettre à jour le mot de passe
                user.set_password(password)
                user.reset_password_token = None
                user.reset_password_token_created = None
                user.save()
                
                # Envoyer un email de confirmation
                subject = "Votre mot de passe a été réinitialisé"
                message = "Votre mot de passe a été réinitialisé avec succès."
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
                
                return Response({
                    'message': 'Mot de passe réinitialisé avec succès.'
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    'error': 'Token ou email invalide.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyTokenView(APIView):
    """
    Endpoint pour vérifier si un token est valide
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        email = request.data.get('email')
        
        if not token:
            return Response({'error': 'Token requis.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if email:
                user = User.objects.get(email=email, reset_password_token=token)
            else:
                user = User.objects.get(reset_password_token=token)
            
            # Vérifier l'expiration
            token_age = timezone.now() - user.reset_password_token_created
            if token_age > timedelta(hours=24):
                return Response({
                    'valid': False,
                    'error': 'Token expiré.'
                }, status=status.HTTP_200_OK)
            
            return Response({
                'valid': True,
                'email': user.email,
                'username': user.username
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Token invalide.'
            }, status=status.HTTP_200_OK)
#  ------ fin -----
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        logout(request)
        return Response({'message': 'تم تسجيل الخروج بنجاح'})

# class UserProfileView(generics.RetrieveUpdateAPIView):
#     serializer_class = UserSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_object(self):
#         return self.request.user


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    def get_object(self):
        return self.request.user
    
    # Optionnel: Pour un meilleur contrôle sur la mise à jour
    def perform_update(self, serializer):
        instance = self.get_object()
        serializer.save()

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




# users/views.py
from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, TeacherProfile, StudentProfile
from .serializers import (
    UserSerializer, 
    TeacherProfileSerializer, 
    StudentProfileSerializer
)

class AdminStudentListView(generics.ListAPIView):
    """
    API pour récupérer tous les étudiants (Admin seulement)
    Requiert un token d'administrateur
    """
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtres possibles
    filterset_fields = {
        'user__grade': ['exact'],
        'enrollment_date': ['exact', 'gte', 'lte'],
    }
    
    search_fields = [
        'user__first_name',
        'user__last_name', 
        'user__username',
        'user__email',
        'parent_name',
        'parent_phone'
    ]
    
    ordering_fields = ['user__first_name', 'user__last_name', 'enrollment_date']
    ordering = ['user__first_name']
    
    def get_queryset(self):
        # Récupérer tous les profils étudiants avec leurs utilisateurs
        queryset = StudentProfile.objects.select_related('user').all()
        
        # Filtrer par rôle student au niveau de la base de données
        queryset = queryset.filter(user__role='student')
        
        # Filtre supplémentaire par statut actif de l'utilisateur
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(user__is_active=is_active_bool)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            
            # Pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            
            return Response({
                'success': True,
                'message': 'تم جلب قائمة الطلاب بنجاح',
                'count': queryset.count(),
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'حدث خطأ أثناء جلب الطلاب: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminTeacherListView(generics.ListAPIView):
    """
    API pour récupérer tous les enseignants (Admin seulement)
    Requiert un token d'administrateur
    """
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtres possibles
    filterset_fields = {
        'is_active': ['exact'],
        'years_of_experience': ['exact', 'gte', 'lte'],
    }
    
    search_fields = [
        'user__first_name',
        'user__last_name', 
        'user__username',
        'user__email',
        'qualification',
        'subjects'
    ]
    
    ordering_fields = ['user__first_name', 'user__last_name', 'years_of_experience']
    ordering = ['user__first_name']
    
    def get_queryset(self):
        # Récupérer tous les profils enseignants avec leurs utilisateurs
        queryset = TeacherProfile.objects.select_related('user').all()
        
        # Filtrer par rôle teacher au niveau de la base de données
        queryset = queryset.filter(user__role='teacher')
        
        # Filtre supplémentaire par statut actif de l'utilisateur
        is_active_user = self.request.query_params.get('user_is_active', None)
        if is_active_user is not None:
            is_active_bool = is_active_user.lower() == 'true'
            queryset = queryset.filter(user__is_active=is_active_bool)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            
            # Pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            
            return Response({
                'success': True,
                'message': 'تم جلب قائمة المعلمين بنجاح',
                'count': queryset.count(),
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'حدث خطأ أثناء جلب المعلمين: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminStudentDetailView(generics.RetrieveAPIView):
    """
    API pour récupérer les détails d'un étudiant spécifique (Admin seulement)
    """
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    lookup_field = 'id'
    
    def get_queryset(self):
        return StudentProfile.objects.select_related('user').filter(user__role='student')


class AdminTeacherDetailView(generics.RetrieveAPIView):
    """
    API pour récupérer les détails d'un enseignant spécifique (Admin seulement)
    """
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    lookup_field = 'id'
    
    def get_queryset(self):
        return TeacherProfile.objects.select_related('user').filter(user__role='teacher')        