"""
curriculum/admin.py
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Subject, Unit, ContentSection

class ContentSectionInline(admin.TabularInline):
    model = ContentSection
    extra = 1
    fields = ('title', 'content_type', 'order', 'preview_content')
    readonly_fields = ('preview_content',)
    
    def preview_content(self, obj):
        content_preview = obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
        return format_html('<div style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">{}</div>', content_preview)
    preview_content.short_description = 'معاينة المحتوى'

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade', 'icon_display', 'color_display', 'is_active', 'unit_count', 'created_at')
    list_filter = ('grade', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    ordering = ('grade', 'name')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'grade', 'is_active')
        }),
        (_('الوصف والمظهر'), {
            'fields': ('description', 'icon', 'color')
        }),
    )
    
    def icon_display(self, obj):
        return format_html('<i class="fa fa-{}"></i> {}', obj.icon, obj.icon) if obj.icon else '-'
    icon_display.short_description = 'الأيقونة'
    
    def color_display(self, obj):
        if obj.color:
            return format_html(
                '<div style="background-color: {}; width: 20px; height: 20px; border-radius: 3px;"></div>',
                obj.color
            )
        return '-'
    color_display.short_description = 'اللون'
    
    def unit_count(self, obj):
        return obj.units.count()
    unit_count.short_description = 'عدد الوحدات'

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'difficulty_display', 'duration_display', 'is_published', 
                    'created_by', 'activity_count', 'created_at')
    list_filter = ('subject', 'difficulty', 'is_published', 'created_at', 'created_by')
    search_fields = ('title', 'description', 'learning_objective')
    list_editable = ('is_published',)
    ordering = ('order', 'created_at')
    raw_id_fields = ('created_by',)
    inlines = [ContentSectionInline]
    
    fieldsets = (
        (None, {
            'fields': ('subject', 'title', 'is_published')
        }),
        (_('المعلومات التعليمية'), {
            'fields': ('description', 'learning_objective', 'difficulty', 'duration_minutes', 'order')
        }),
        (_('الوسائط المتعددة'), {
            'fields': ('thumbnail', 'video_url', 'audio_url'),
            'classes': ('collapse',)
        }),
        (_('المعلومات الإضافية'), {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def difficulty_display(self, obj):
        colors = {
            'easy': 'green',
            'medium': 'orange',
            'hard': 'red'
        }
        color = colors.get(obj.difficulty, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_difficulty_display()
        )
    difficulty_display.short_description = 'الصعوبة'
    
    def duration_display(self, obj):
        return f'{obj.duration_minutes} دقيقة'
    duration_display.short_description = 'المدة'
    
    def activity_count(self, obj):
        return obj.activities.count()
    activity_count.short_description = 'عدد الأنشطة'
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ContentSection)
class ContentSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit', 'content_type_display', 'order', 'content_preview')
    list_filter = ('content_type', 'unit__subject')
    search_fields = ('title', 'content', 'unit__title')
    ordering = ('unit', 'order')
    raw_id_fields = ('unit',)
    
    fieldsets = (
        (None, {
            'fields': ('unit', 'title', 'order')
        }),
        (_('المحتوى'), {
            'fields': ('content_type', 'content', 'metadata')
        }),
    )
    
    def content_type_display(self, obj):
        colors = {
            'text': 'blue',
            'image': 'green',
            'video': 'red',
            'audio': 'purple',
            'interactive': 'orange'
        }
        color = colors.get(obj.content_type, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_content_type_display()
        )
    content_type_display.short_description = 'نوع المحتوى'
    
    def content_preview(self, obj):
        preview = obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
        return format_html('<div style="max-width: 300px;">{}</div>', preview)
    content_preview.short_description = 'معاينة المحتوى'