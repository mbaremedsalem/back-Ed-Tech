"""
users/admin.py
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, TeacherProfile, StudentProfile

class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    can_delete = False
    verbose_name_plural = 'ملف المعلم'
    fields = ('subjects', 'years_of_experience', 'qualification', 'is_active')
    extra = 0

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'ملف الطالب'
    fields = ('parent_name', 'parent_phone', 'address')
    extra = 0

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'grade', 'school', 'is_active')
    list_filter = ('role', 'grade', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'school')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('المعلومات الشخصية'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_image')}),
        (_('المعلومات الأكاديمية'), {'fields': ('role', 'grade', 'school', 'date_of_birth')}),
        (_('الصلاحيات'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('تواريخ مهمة'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'grade'),
        }),
    )
    
    def get_inline_instances(self, request, obj=None):
        inlines = []
        if obj and obj.role == 'teacher':
            inlines.append(TeacherProfileInline)
        elif obj and obj.role == 'student':
            inlines.append(StudentProfileInline)
        return [inline(self.model, self.admin_site) for inline in inlines]
    
    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            yield inline.get_formset(request, obj), inline

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'subjects', 'years_of_experience', 'qualification', 'is_active')
    list_filter = ('is_active', 'years_of_experience')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'subjects', 'qualification')
    raw_id_fields = ('user',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'is_active')
        }),
        (_('المعلومات المهنية'), {
            'fields': ('subjects', 'years_of_experience', 'qualification')
        }),
    )

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'parent_name', 'parent_phone', 'enrollment_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'parent_name', 'parent_phone')
    list_filter = ('enrollment_date',)
    raw_id_fields = ('user',)
    
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        (_('معلومات ولي الأمر'), {
            'fields': ('parent_name', 'parent_phone')
        }),
        (_('معلومات إضافية'), {
            'fields': ('address', 'enrollment_date')
        }),
    )

admin.site.register(User, CustomUserAdmin)