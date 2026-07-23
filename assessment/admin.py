"""
assessment/admin.py
"""

from django.contrib import admin

from .models import Error, StudentProgress, LogAnswer


@admin.register(Error)
class ErrorAdmin(admin.ModelAdmin):
    list_display = ('code', 'error_type', 'category', 'severity_level', 'skill')
    list_filter = ('category', 'severity_level', 'skill__goal__lesson__unit__subject')
    search_fields = ('code', 'error_type', 'root_cause')
    autocomplete_fields = ('skill',)


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'skill', 'status', 'mastery', 'attempts',
        'correct_count', 'consecutive_correct', 'last_activity',
    )
    list_filter = ('status', 'skill__goal__lesson__unit__subject')
    search_fields = ('student__username', 'skill__code')
    autocomplete_fields = ('student', 'skill')
    readonly_fields = ('last_activity',)


@admin.register(LogAnswer)
class LogAnswerAdmin(admin.ModelAdmin):
    """
    Lecture seule dans l'admin : log_answers est append-only,
    la modification et la suppression sont interdites au niveau modèle.
    """
    list_display = ('timestamp', 'student', 'chunk', 'is_correct', 'error_type', 'time_taken')
    list_filter = ('is_correct', 'error_type')
    search_fields = ('student__username', 'chunk__code')
    autocomplete_fields = ('student', 'skill', 'chunk', 'error_detail')
    readonly_fields = [f.name for f in LogAnswer._meta.fields]

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
