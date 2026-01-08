"""
users/serializers.py
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, TeacherProfile, StudentProfile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'phone_number', 'profile_image', 'grade', 'school',
            'date_joined', 'last_login', 'is_active'
        ]
        read_only_fields = ('id', 'date_joined', 'last_login', 'is_active')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'role',
            'password', 'password_confirm', 'phone_number', 'grade', 'school'
        ]
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("كلمات المرور غير متطابقة")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
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