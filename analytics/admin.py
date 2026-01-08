"""
analytics/admin.py
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import LearningAnalytics, TeacherDashboard, SystemLog

@admin.register(LearningAnalytics)
class LearningAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'total_time_spent_display', 'completed_units', 
                    'total_score', 'avg_mastery_level_display')
    list_filter = ('date', 'student__role', 'student__grade')
    search_fields = ('student__username', 'student__first_name', 'student__last_name')
    ordering = ('-date',)
    raw_id_fields = ('student',)
    date_hierarchy = 'date'
    
    fieldsets = (
        (None, {
            'fields': ('student', 'date')
        }),
        (_('الإحصائيات'), {
            'fields': ('total_time_spent', 'completed_units', 'total_score', 'avg_mastery_level')
        }),
    )
    
    def total_time_spent_display(self, obj):
        hours = obj.total_time_spent // 60
        minutes = obj.total_time_spent % 60
        if hours > 0:
            return f'{hours} ساعة {minutes} دقيقة'
        return f'{minutes} دقيقة'
    total_time_spent_display.short_description = 'الوقت الإجمالي'
    
    def avg_mastery_level_display(self, obj):
        if obj.avg_mastery_level >= 90:
            color = 'green'
            text = 'ممتاز'
        elif obj.avg_mastery_level >= 70:
            color = 'blue'
            text = 'جيد جداً'
        elif obj.avg_mastery_level >= 50:
            color = 'orange'
            text = 'متوسط'
        else:
            color = 'red'
            text = 'ضعيف'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}% ({})</span>',
            color, int(obj.avg_mastery_level), text
        )
    avg_mastery_level_display.short_description = 'متوسط الإتقان'

@admin.register(TeacherDashboard)
class TeacherDashboardAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'total_students', 'active_students', 'total_units_created', 
                    'student_engagement_rate_display', 'avg_student_progress_display', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('teacher__username', 'teacher__first_name', 'teacher__last_name')
    ordering = ('-last_updated',)
    raw_id_fields = ('teacher',)
    readonly_fields = ('last_updated',)
    
    fieldsets = (
        (None, {
            'fields': ('teacher',)
        }),
        (_('إحصائيات المعلم'), {
            'fields': ('total_students', 'active_students', 'total_units_created')
        }),
        (_('مؤشرات الأداء'), {
            'fields': ('student_engagement_rate', 'avg_student_progress')
        }),
        (_('معلومات التحديث'), {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )
    
    def student_engagement_rate_display(self, obj):
        if obj.student_engagement_rate >= 80:
            color = 'green'
        elif obj.student_engagement_rate >= 60:
            color = 'blue'
        elif obj.student_engagement_rate >= 40:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, int(obj.student_engagement_rate)
        )
    student_engagement_rate_display.short_description = 'معدل التفاعل'
    
    def avg_student_progress_display(self, obj):
        if obj.avg_student_progress >= 80:
            color = 'green'
        elif obj.avg_student_progress >= 60:
            color = 'blue'
        elif obj.avg_student_progress >= 40:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, int(obj.avg_student_progress)
        )
    avg_student_progress_display.short_description = 'متوسط التقدم'

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('level_display', 'category_display', 'message_preview', 'user', 
                    'ip_address', 'created_at')
    list_filter = ('level', 'category', 'created_at')
    search_fields = ('message', 'user__username', 'ip_address')
    ordering = ('-created_at',)
    raw_id_fields = ('user',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('level', 'category', 'message')
        }),
        (_('معلومات المستخدم'), {
            'fields': ('user', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        (_('المعلومات الزمنية'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def level_display(self, obj):
        colors = {
            'info': 'blue',
            'warning': 'orange',
            'error': 'red',
            'security': 'purple'
        }
        color = colors.get(obj.level, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_level_display()
        )
    level_display.short_description = 'المستوى'
    
    def category_display(self, obj):
        icons = {
            'user': '👤',
            'content': '📄',
            'assessment': '🎯',
            'system': '⚙️'
        }
        icon = icons.get(obj.category, '📌')
        return format_html(
            '{} {}',
            icon,
            obj.get_category_display()
        )
    category_display.short_description = 'الفئة'
    
    def message_preview(self, obj):
        preview = obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
        return format_html('<div style="max-width: 300px;">{}</div>', preview)
    message_preview.short_description = 'الرسالة'
    
    def has_add_permission(self, request):
        return False  # منع الإضافة يدوياً
    
    def has_change_permission(self, request, obj=None):
        return False  # منع التعديل
    
    actions = ['delete_selected']