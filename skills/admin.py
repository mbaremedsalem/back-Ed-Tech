"""
skills/admin.py
"""

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Skill, Prerequisite, Chunk


class ChunkInline(admin.TabularInline):
    model = Chunk
    extra = 0
    fields = ('code', 'chunk_type', 'title', 'order_index', 'points')


class PrerequisiteInline(admin.TabularInline):
    model = Prerequisite
    fk_name = 'skill'
    extra = 0
    autocomplete_fields = ('prerequisite',)
    verbose_name = _('متطلب سابق')
    verbose_name_plural = _('المتطلبات السابقة')


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'name', 'skill_type', 'goal', 'difficulty',
        'mastery_threshold', 'chunks_status',
    )
    list_filter = ('skill_type', 'difficulty', 'goal__lesson__unit__subject')
    search_fields = ('code', 'name')
    autocomplete_fields = ('goal',)
    inlines = [ChunkInline, PrerequisiteInline]

    @admin.display(description=_('اكتمال القطع'))
    def chunks_status(self, obj):
        return '✅' if obj.chunks_meet_minimum() else '⚠️ غير مكتمل'

    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()
        except ValidationError as e:
            form.add_error(None, e)
            return
        super().save_model(request, obj, form, change)


@admin.register(Prerequisite)
class PrerequisiteAdmin(admin.ModelAdmin):
    list_display = ('skill', 'prerequisite')
    search_fields = ('skill__code', 'prerequisite__code')
    autocomplete_fields = ('skill', 'prerequisite')


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ('code', 'chunk_type', 'skill', 'order_index', 'points', 'difficulty')
    list_filter = ('chunk_type', 'difficulty', 'skill__goal__lesson__unit__subject')
    search_fields = ('code', 'title', 'content')
    autocomplete_fields = ('skill',)
