"""
users/serializers.py
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, TeacherProfile, StudentProfile,Wilaya




# serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User, TeacherProfile, StudentProfile

class AdminRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'phone_number',
            'role', 'is_staff', 'is_superuser'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'is_staff': {'read_only': True},
            'is_superuser': {'read_only': True},
        }
    
    def validate(self, attrs):
        # Vérifier que les mots de passe correspondent
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "كلمات المرور غير متطابقة"})
        
        # Vérifier le rôle - pour l'inscription admin, forcer le rôle admin
        role = attrs.get('role', 'admin')
        if role != 'admin':
            raise serializers.ValidationError({"role": "هذا الـ API مخصص فقط لإنشاء حسابات المديرين"})
        
        # Vérifier si l'email existe déjà
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "البريد الإلكتروني مسجل بالفعل"})
        
        # Vérifier si le nom المستخدم موجود déjà
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "اسم المستخدم مسجل بالفعل"})
        
        return attrs
    
    def create(self, validated_data):
        # Retirer password2 des données
        password2 = validated_data.pop('password2')
        password = validated_data.pop('password')
        
        # Forcer les valeurs pour un admin
        validated_data['role'] = 'admin'
        validated_data['is_staff'] = True
        validated_data['is_superuser'] = True
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        return user
# --------debit -------
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django_rest_passwordreset.serializers import PasswordTokenSerializer
from django_rest_passwordreset.models import ResetPasswordToken

User = get_user_model()

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class CustomPasswordTokenSerializer(PasswordTokenSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Les mots de passe ne correspondent pas."})
        return data

class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Aucun utilisateur trouvé avec cet email.")
        return value
    # -------- fin debit -------

class UserSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_empty_file=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'phone_number', 'profile_image', 'grade', 'school',
            'date_joined', 'last_login', 'is_active'
        ]
        read_only_fields = ('id', 'date_joined', 'last_login', 'is_active')
        
    def update(self, instance, validated_data):
        # Handle profile image separately if needed
        profile_image = validated_data.pop('profile_image', None)
        
        # Update all other fields
        instance = super().update(instance, validated_data)
        
        # Update profile image if provided
        if profile_image is not None:
            instance.profile_image = profile_image
            instance.save()
            
        return instance

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = [
#             'id', 'username', 'email', 'first_name', 'last_name', 
#             'role', 'phone_number', 'profile_image', 'grade', 'school',
#             'date_joined', 'last_login', 'is_active'
#         ]
#         read_only_fields = ('id', 'date_joined', 'last_login', 'is_active')
# users/serializers.py



class WilayaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wilaya
        fields = ['id', 'code', 'name']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)
    wilaya_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'role',
            'password', 'password_confirm', 'phone_number', 'grade', 'school',
            'wilaya_id'
        ]
    
    def validate(self, data):
        # Vérifier la correspondance des mots de passe
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "كلمات المرور غير متطابقة"})
        
        # Validation pour le rôle student - wilaya obligatoire
        role = data.get('role')
        wilaya_id = data.get('wilaya_id')
        
        if role == 'student' and not wilaya_id:
            raise serializers.ValidationError({"wilaya_id": "الطالب يجب أن ينتمي إلى ولاية."})
        
        # Si wilaya_id est fourni, vérifier qu'elle existe
        if wilaya_id:
            try:
                Wilaya.objects.get(id=wilaya_id)
            except Wilaya.DoesNotExist:
                raise serializers.ValidationError({"wilaya_id": "الولاية المحددة غير موجودة."})
        
        return data
    
    def create(self, validated_data):
        # Retirer password_confirm et wilaya_id des données validées
        validated_data.pop('password_confirm')
        wilaya_id = validated_data.pop('wilaya_id', None)
        
        # Créer l'utilisateur
        user = User.objects.create_user(**validated_data)
        
        # Assigner la wilaya si fournie
        if wilaya_id:
            user.wilaya_id = wilaya_id
            user.save()
        
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("اسم المستخدم أو كلمة المرور غير صحيحة")
        if not user.is_active:
            raise serializers.ValidationError("الحساب غير نشط")
        data['user'] = user
        return data

class TeacherProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TeacherProfile
        fields = '__all__'

class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = StudentProfile
        fields = '__all__'