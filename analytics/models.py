"""
analytics/models.py
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User
from curriculum.models import Unit, Subject

class LearningAnalytics(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField(_('التاريخ'))
    total_time_spent = models.IntegerField(_('إجمالي الوقت بالدقائق'), default=0)
    completed_units = models.IntegerField(_('الوحدات المكتملة'), default=0)
    total_score = models.IntegerField(_('إجمالي النقاط'), default=0)
    avg_mastery_level = models.FloatField(_('متوسط مستوى الإتقان'), default=0.0)
    
    class Meta:
        verbose_name = _('تحليل التعلم')
        verbose_name_plural = _('تحليلات التعلم')
        unique_together = ['student', 'date']
    
    def __str__(self):
        return f"{self.student.username} - {self.date}"

class TeacherDashboard(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard')
    total_students = models.IntegerField(_('إجمالي الطلاب'), default=0)
    active_students = models.IntegerField(_('الطلاب النشطين'), default=0)
    total_units_created = models.IntegerField(_('إجمالي الوحدات المنشأة'), default=0)
    student_engagement_rate = models.FloatField(_('معدل تفاعل الطلاب'), default=0.0)
    avg_student_progress = models.FloatField(_('متوسط تقدم الطلاب'), default=0.0)
    last_updated = models.DateTimeField(_('آخر تحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('لوحة تحكم المعلم')
        verbose_name_plural = _('لوحات تحكم المعلمين')
    
    def __str__(self):
        return f"لوحة تحكم {self.teacher.username}"

class SystemLog(models.Model):
    LOG_LEVELS = (
        ('info', 'معلومات'),
        ('warning', 'تحذير'),
        ('error', 'خطأ'),
        ('security', 'أمن'),
    )
    
    LOG_CATEGORIES = (
        ('user', 'مستخدم'),
        ('content', 'محتوى'),
        ('assessment', 'تقييم'),
        ('system', 'نظام'),
    )
    
    level = models.CharField(_('مستوى السجل'), max_length=20, choices=LOG_LEVELS)
    category = models.CharField(_('الفئة'), max_length=20, choices=LOG_CATEGORIES)
    message = models.TextField(_('الرسالة'))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(_('عنوان IP'), null=True, blank=True)
    user_agent = models.TextField(_('وكيل المستخدم'), blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('سجل النظام')
        verbose_name_plural = _('سجلات النظام')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_level_display()} - {self.message[:50]}"