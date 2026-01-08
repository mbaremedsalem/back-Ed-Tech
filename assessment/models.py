# """
# assessment/models.py
# """

# from django.db import models
# from django.utils.translation import gettext_lazy as _
# from users.models import User
# from curriculum.models import Unit

# class Activity(models.Model):
#     ACTIVITY_TYPES = (
#         ('multiple_choice', 'اختيار من متعدد'),
#         ('true_false', 'صح أو خطأ'),
#         ('matching', 'توصيل'),
#         ('drag_drop', 'سحب وإفلات'),
#         ('fill_blank', 'ملء الفراغات'),
#         ('short_answer', 'إجابة قصيرة'),
#     )
    
#     unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='activities')
#     title = models.CharField(_('عنوان النشاط'), max_length=200)
#     activity_type = models.CharField(_('نوع النشاط'), max_length=50, choices=ACTIVITY_TYPES)
#     question = models.TextField(_('السؤال'))
#     options = models.JSONField(_('الخيارات'), default=list, blank=True)
#     correct_answer = models.JSONField(_('الإجابة الصحيحة'))
#     points = models.IntegerField(_('النقاط'), default=10)
#     explanation = models.TextField(_('التفسير'), blank=True)
#     time_limit = models.IntegerField(_('الحد الزمني بالثواني'), null=True, blank=True)
#     order = models.IntegerField(_('الترتيب'), default=0)
#     is_active = models.BooleanField(_('نشط'), default=True)
    
#     class Meta:
#         verbose_name = _('نشاط')
#         verbose_name_plural = _('الأنشطة')
#         ordering = ['order']
    
#     def __str__(self):
#         return f"{self.title} - {self.get_activity_type_display()}"

# class StudentAttempt(models.Model):
#     student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
#     activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='attempts')
#     answer = models.JSONField(_('إجابة الطالب'))
#     is_correct = models.BooleanField(_('إجابة صحيحة'), default=False)
#     score = models.IntegerField(_('الدرجة'), default=0)
#     time_taken = models.IntegerField(_('الوقت المستغرق بالثواني'))
#     attempted_at = models.DateTimeField(_('تاريخ المحاولة'), auto_now_add=True)
    
#     class Meta:
#         verbose_name = _('محاولة الطالب')
#         verbose_name_plural = _('محاولات الطلاب')
#         ordering = ['-attempted_at']
    
#     def __str__(self):
#         return f"{self.student.username} - {self.activity.title}"

# class StudentProgress(models.Model):
#     MASTERY_LEVELS = (
#         ('not_started', 'لم يبدأ'),
#         ('beginner', 'مبتدئ'),
#         ('intermediate', 'متوسط'),
#         ('advanced', 'متقدم'),
#         ('mastered', 'أتقن'),
#     )
    
#     student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
#     unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='student_progress')
#     completed_activities = models.ManyToManyField(Activity, blank=True, related_name='completed_by')
#     total_score = models.IntegerField(_('إجمالي النقاط'), default=0)
#     mastery_level = models.CharField(_('مستوى الإتقان'), max_length=20, choices=MASTERY_LEVELS, default='not_started')
#     completion_percentage = models.FloatField(_('نسبة الإنجاز'), default=0.0)
#     last_accessed = models.DateTimeField(_('آخر وصول'), auto_now=True)
#     started_at = models.DateTimeField(_('تاريخ البدء'), auto_now_add=True)
#     completed_at = models.DateTimeField(_('تاريخ الإكمال'), null=True, blank=True)
    
#     class Meta:
#         verbose_name = _('تقدم الطالب')
#         verbose_name_plural = _('تقدم الطلاب')
#         unique_together = ['student', 'unit']
    
#     def __str__(self):
#         return f"{self.student.username} - {self.unit.title}"
    
#     def update_progress(self):
#         total_activities = self.unit.activities.filter(is_active=True).count()
#         completed_count = self.completed_activities.count()
        
#         if total_activities > 0:
#             self.completion_percentage = (completed_count / total_activities) * 100
#         else:
#             self.completion_percentage = 0
        
#         # تحديث مستوى الإتقان بناءً على النسبة
#         if self.completion_percentage >= 90:
#             self.mastery_level = 'mastered'
#         elif self.completion_percentage >= 70:
#             self.mastery_level = 'advanced'
#         elif self.completion_percentage >= 50:
#             self.mastery_level = 'intermediate'
#         elif self.completion_percentage > 0:
#             self.mastery_level = 'beginner'
        
#         self.save()




"""
assessment/models.py
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User
from curriculum.models import Unit

class Activity(models.Model):
    ACTIVITY_TYPES = (
        ('multiple_choice', 'اختيار من متعدد'),
        ('true_false', 'صح أو خطأ'),
        ('matching', 'توصيل'),
        ('drag_drop', 'سحب وإفلات'),
        ('fill_blank', 'ملء الفراغات'),
        ('short_answer', 'إجابة قصيرة'),
    )
    
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='activities')
    title = models.CharField(_('عنوان النشاط'), max_length=200)
    activity_type = models.CharField(_('نوع النشاط'), max_length=50, choices=ACTIVITY_TYPES)
    question = models.TextField(_('السؤال'))
    options = models.JSONField(_('الخيارات'), default=list, blank=True)
    correct_answer = models.JSONField(_('الإجابة الصحيحة'))
    points = models.IntegerField(_('النقاط'), default=10)
    explanation = models.TextField(_('التفسير'), blank=True)
    time_limit = models.IntegerField(_('الحد الزمني بالثواني'), null=True, blank=True)
    order = models.IntegerField(_('الترتيب'), default=0)
    is_active = models.BooleanField(_('نشط'), default=True)
    
    class Meta:
        verbose_name = _('نشاط')
        verbose_name_plural = _('الأنشطة')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.title} - {self.get_activity_type_display()}"

class StudentAttempt(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='attempts')
    answer = models.JSONField(_('إجابة الطالب'))
    is_correct = models.BooleanField(_('إجابة صحيحة'), default=False)
    score = models.IntegerField(_('الدرجة'), default=0)
    time_taken = models.IntegerField(_('الوقت المستغرق بالثواني'))
    attempted_at = models.DateTimeField(_('تاريخ المحاولة'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('محاولة الطالب')
        verbose_name_plural = _('محاولات الطلاب')
        ordering = ['-attempted_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.activity.title}"

class StudentProgress(models.Model):
    MASTERY_LEVELS = (
        ('not_started', 'لم يبدأ'),
        ('beginner', 'مبتدئ'),
        ('intermediate', 'متوسط'),
        ('advanced', 'متقدم'),
        ('mastered', 'أتقن'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='student_progress')
    completed_activities = models.ManyToManyField(Activity, blank=True, related_name='completed_by')
    total_score = models.IntegerField(_('إجمالي النقاط'), default=0)
    mastery_level = models.CharField(_('مستوى الإتقان'), max_length=20, choices=MASTERY_LEVELS, default='not_started')
    completion_percentage = models.FloatField(_('نسبة الإنجاز'), default=0.0)
    last_accessed = models.DateTimeField(_('آخر وصول'), auto_now=True)
    started_at = models.DateTimeField(_('تاريخ البدء'), auto_now_add=True)
    completed_at = models.DateTimeField(_('تاريخ الإكمال'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('تقدم الطالب')
        verbose_name_plural = _('تقدم الطلاب')
        unique_together = ['student', 'unit']
    
    def __str__(self):
        return f"{self.student.username} - {self.unit.title}"
    
    def update_progress(self):
        total_activities = self.unit.activities.filter(is_active=True).count()
        completed_count = self.completed_activities.count()
        
        if total_activities > 0:
            self.completion_percentage = (completed_count / total_activities) * 100
        else:
            self.completion_percentage = 0
        
        # تحديث مستوى الإتقان بناءً على النسبة
        if self.completion_percentage >= 90:
            self.mastery_level = 'mastered'
        elif self.completion_percentage >= 70:
            self.mastery_level = 'advanced'
        elif self.completion_percentage >= 50:
            self.mastery_level = 'intermediate'
        elif self.completion_percentage > 0:
            self.mastery_level = 'beginner'
        
        self.save()