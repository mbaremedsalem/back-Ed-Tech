"""
curriculum/models.py
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User

class Subject(models.Model):
    name = models.CharField(_('اسم المادة'), max_length=100)
    grade = models.IntegerField(_('الصف الدراسي'))
    description = models.TextField(_('الوصف'), blank=True)
    icon = models.CharField(_('الأيقونة'), max_length=50, blank=True)
    color = models.CharField(_('اللون'), max_length=20, blank=True)
    is_active = models.BooleanField(_('نشط'), default=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('مادة')
        verbose_name_plural = _('المواد')
        unique_together = ['name', 'grade']
    
    def __str__(self):
        return f"{self.name} - الصف {self.grade}"

class Unit(models.Model):
    DIFFICULTY_LEVELS = (
        ('easy', 'سهل'),
        ('medium', 'متوسط'),
        ('hard', 'صعب'),
    )
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='units')
    title = models.CharField(_('العنوان'), max_length=200)
    description = models.TextField(_('الوصف'), blank=True)
    learning_objective = models.TextField(_('الهدف التعليمي'))
    duration_minutes = models.IntegerField(_('المدة بالدقائق'), default=15)
    difficulty = models.CharField(_('مستوى الصعوبة'), max_length=20, choices=DIFFICULTY_LEVELS, default='medium')
    order = models.IntegerField(_('الترتيب'), default=0)
    thumbnail = models.ImageField(_('الصورة المصغرة'), upload_to='units/', null=True, blank=True)
    video_url = models.URLField(_('رابط الفيديو'), blank=True)
    audio_url = models.URLField(_('رابط الصوت'), blank=True)
    is_published = models.BooleanField(_('منشور'), default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_units')
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    
    class Meta:
        verbose_name = _('وحدة تعليمية')
        verbose_name_plural = _('الوحدات التعليمية')
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.title} - {self.subject.name}"

class ContentSection(models.Model):
    CONTENT_TYPES = (
        ('text', 'نص'),
        ('image', 'صورة'),
        ('video', 'فيديو'),
        ('audio', 'صوت'),
        ('interactive', 'تفاعلي'),
    )
    
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(_('عنوان القسم'), max_length=200)
    content_type = models.CharField(_('نوع المحتوى'), max_length=20, choices=CONTENT_TYPES)
    content = models.TextField(_('المحتوى'))
    order = models.IntegerField(_('الترتيب'), default=0)
    metadata = models.JSONField(_('البيانات الوصفية'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('قسم المحتوى')
        verbose_name_plural = _('أقسام المحتوى')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.title} - {self.get_content_type_display()}"