from django.db import models

# Create your models here.

"""
users/models.py
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

# users/models.py - Ajoutez ce modèle avant la classe User

class Wilaya(models.Model):
    """
    Modèle pour les wilayas de Mauritanie
    """
    code = models.IntegerField(_('code'), unique=True)
    name = models.CharField(_('nom'), max_length=100)
    
    class Meta:
        verbose_name = _('ولاية')
        verbose_name_plural = _('الولايات')
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'مدير النظام'),
        ('teacher', 'معلم'),
        ('student', 'طالب'),
    )
    
    role = models.CharField(_('الدور'), max_length=20, choices=ROLE_CHOICES, default='student')
    phone_number = models.CharField(_('رقم الهاتف'), max_length=15, blank=True)
    profile_image = models.ImageField(_('صورة الملف الشخصي'), upload_to='profiles/', null=True, blank=True)
    date_of_birth = models.DateField(_('تاريخ الميلاد'), null=True, blank=True)
    grade = models.IntegerField(_('الصف الدراسي'), null=True, blank=True)
    school = models.CharField(_('المدرسة'), max_length=255, blank=True)
    # Nouveau champ wilaya
    wilaya = models.ForeignKey(
        Wilaya, 
        on_delete=models.SET_NULL, 
        verbose_name=_('الولاية'),
        null=True, 
        blank=True,
        related_name='users'
    )
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
        
    # Champs pour reset password
    reset_password_token = models.CharField(max_length=100, blank=True, null=True)
    reset_password_token_created = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمين')
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    subjects = models.CharField(_('المواد الدراسية'), max_length=255)
    years_of_experience = models.IntegerField(_('سنوات الخبرة'), default=0)
    qualification = models.CharField(_('المؤهل العلمي'), max_length=255, blank=True)
    is_active = models.BooleanField(_('نشط'), default=True)
    
    class Meta:
        verbose_name = _('ملف المعلم')
        verbose_name_plural = _('ملفات المعلمين')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - معلم"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    parent_name = models.CharField(_('اسم ولي الأمر'), max_length=255, blank=True)
    parent_phone = models.CharField(_('هاتف ولي الأمر'), max_length=15, blank=True)
    address = models.TextField(_('العنوان'), blank=True)
    enrollment_date = models.DateField(_('تاريخ التسجيل'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('ملف الطالب')
        verbose_name_plural = _('ملفات الطلاب')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - طالب"