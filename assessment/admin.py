"""
assessment/admin.py
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django import forms
from .models import Activity, StudentAttempt, StudentProgress

class ActivityAdminForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = '__all__'
        widgets = {
            'question': forms.Textarea(attrs={'rows': 3}),
            'explanation': forms.Textarea(attrs={'rows': 2}),
            'options': forms.Textarea(attrs={'rows': 3}),  # facultatif, pour JSON lisible
        }

    def clean_options(self):
        data = self.cleaned_data.get('options')
        if data in (None, ''):
            return []  # valeur par défaut si vide
        return data

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    form = ActivityAdminForm
    list_display = ('title', 'unit', 'activity_type_display', 'points', 'time_limit_display', 
                    'is_active', 'order', 'attempt_count')
    list_filter = ('activity_type', 'is_active', 'unit__subject')
    search_fields = ('title', 'question', 'unit__title')
    list_editable = ('is_active', 'order', 'points')
    ordering = ('unit', 'order')
    raw_id_fields = ('unit',)
    
    fieldsets = (
        (None, {
            'fields': ('unit', 'title', 'is_active', 'order')
        }),
        (_('معلومات النشاط'), {
            'fields': ('activity_type', 'question', 'points', 'time_limit', 'explanation')
        }),
        (_('الإجابات والخيارات'), {
            'fields': ('options', 'correct_answer'),
            'classes': ('collapse',)
        }),
    )
    
    def activity_type_display(self, obj):
        colors = {
            'multiple_choice': 'blue',
            'true_false': 'green',
            'matching': 'orange',
            'drag_drop': 'purple',
            'fill_blank': 'red',
            'short_answer': 'brown'
        }
        color = colors.get(obj.activity_type, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_activity_type_display()
        )
    activity_type_display.short_description = 'نوع النشاط'
    
    def time_limit_display(self, obj):
        if obj.time_limit:
            return f'{obj.time_limit} ثانية'
        return 'لا يوجد'
    time_limit_display.short_description = 'الحد الزمني'
    
    def attempt_count(self, obj):
        return obj.attempts.count()
    attempt_count.short_description = 'عدد المحاولات'

class StudentAttemptAdminForm(forms.ModelForm):
    class Meta:
        model = StudentAttempt
        fields = '__all__'
        widgets = {
            'answer': forms.Textarea(attrs={'rows': 2}),
        }

@admin.register(StudentAttempt)
class StudentAttemptAdmin(admin.ModelAdmin):
    form = StudentAttemptAdminForm
    list_display = ('student', 'activity', 'is_correct_display', 'score', 'time_taken_display', 
                    'attempted_at')
    list_filter = ('is_correct', 'attempted_at', 'activity__unit__subject')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 
                     'activity__title')
    ordering = ('-attempted_at',)
    raw_id_fields = ('student', 'activity')
    readonly_fields = ('attempted_at',)
    
    fieldsets = (
        (None, {
            'fields': ('student', 'activity')
        }),
        (_('نتيجة المحاولة'), {
            'fields': ('answer', 'is_correct', 'score', 'time_taken')
        }),
        (_('المعلومات الزمنية'), {
            'fields': ('attempted_at',),
            'classes': ('collapse',)
        }),
    )
    
    def is_correct_display(self, obj):
        if obj.is_correct:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ صحيحة</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ خاطئة</span>'
        )
    is_correct_display.short_description = 'الحالة'
    
    def time_taken_display(self, obj):
        return f'{obj.time_taken} ثانية'
    time_taken_display.short_description = 'الوقت المستغرق'

class StudentProgressAdminForm(forms.ModelForm):
    class Meta:
        model = StudentProgress
        fields = '__all__'

@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    form = StudentProgressAdminForm
    list_display = ('student', 'unit', 'mastery_level_display', 'completion_percentage_display', 
                    'total_score', 'completed_activities_count', 'last_accessed')
    list_filter = ('mastery_level', 'unit__subject', 'last_accessed')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 
                     'unit__title')
    ordering = ('-last_accessed',)
    raw_id_fields = ('student', 'unit')
    filter_horizontal = ('completed_activities',)
    readonly_fields = ('last_accessed', 'started_at')
    
    fieldsets = (
        (None, {
            'fields': ('student', 'unit')
        }),
        (_('تقدم الطالب'), {
            'fields': ('completed_activities', 'total_score', 'mastery_level', 'completion_percentage')
        }),
        (_('المعلومات الزمنية'), {
            'fields': ('started_at', 'last_accessed', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def mastery_level_display(self, obj):
        colors = {
            'not_started': 'gray',
            'beginner': 'red',
            'intermediate': 'orange',
            'advanced': 'blue',
            'mastered': 'green'
        }
        color = colors.get(obj.mastery_level, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_mastery_level_display()
        )
    mastery_level_display.short_description = 'مستوى الإتقان'
    
    def completion_percentage_display(self, obj):
        if obj.completion_percentage == 100:
            color = 'green'
        elif obj.completion_percentage >= 70:
            color = 'blue'
        elif obj.completion_percentage >= 50:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<div style="background: #f0f0f0; border-radius: 3px; height: 20px; width: 100px; position: relative;">'
            '<div style="background: {}; width: {}%; height: 100%; border-radius: 3px;"></div>'
            '<span style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; '
            'text-align: center; line-height: 20px; font-size: 12px; color: #333;">{}%</span>'
            '</div>',
            color, obj.completion_percentage, int(obj.completion_percentage)
        )
    completion_percentage_display.short_description = 'نسبة الإنجاز'
    
    def completed_activities_count(self, obj):
        return obj.completed_activities.count()
    completed_activities_count.short_description = 'الأنشطة المكتملة'