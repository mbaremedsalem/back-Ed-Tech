"""
core/signals.py
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from users.models import TeacherProfile, StudentProfile
from analytics.models import SystemLog

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """إنشاء ملف تعريف تلقائي عند إنشاء مستخدم جديد"""
    if created:
        if instance.role == 'teacher':
            TeacherProfile.objects.create(user=instance)
        elif instance.role == 'student':
            StudentProfile.objects.create(user=instance)
        
        # تسجيل الحدث
        SystemLog.objects.create(
            level='info',
            category='user',
            message=f'تم إنشاء مستخدم جديد: {instance.username}',
            user=instance
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """حفظ ملف التعريف عند تحديث المستخدم"""
    try:
        if instance.role == 'teacher':
            instance.teacher_profile.save()
        elif instance.role == 'student':
            instance.student_profile.save()
    except:
        pass

@receiver(pre_save, sender=User)
def log_user_changes(sender, instance, **kwargs):
    """تسجيل تغييرات المستخدم المهمة"""
    if instance.pk:
        try:
            old_user = User.objects.get(pk=instance.pk)
            
            # التحقق من التغييرات المهمة
            changes = []
            if old_user.is_active != instance.is_active:
                status = 'مفعل' if instance.is_active else 'معطل'
                changes.append(f'تغيير حالة الحساب إلى: {status}')
            
            if old_user.role != instance.role:
                changes.append(f'تغيير الدور من {old_user.role} إلى {instance.role}')
            
            if changes:
                SystemLog.objects.create(
                    level='info',
                    category='user',
                    message=f'تغييرات على مستخدم {instance.username}: {", ".join(changes)}',
                    user=instance
                )
        except User.DoesNotExist:
            pass

@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """تسجيل حذف المستخدم"""
    SystemLog.objects.create(
        level='warning',
        category='user',
        message=f'تم حذف المستخدم: {instance.username}',
        user=None  # المستخدم محذوف
    )