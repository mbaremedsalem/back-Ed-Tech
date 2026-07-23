"""
users/admin.py
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User, Wilaya, StudentProfile, TeacherProfile


@admin.register(Wilaya)
class WilayaAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
    ordering = ('code',)


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    fk_name = 'user'
    extra = 0
    verbose_name_plural = 'ملف الطالب'


class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    can_delete = False
    fk_name = 'user'
    extra = 0
    verbose_name_plural = 'ملف المعلم'


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'role', 'wilaya', 'is_active', 'is_staff', 'date_joined',
    )
    list_filter = ('role', 'wilaya', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            'FATIN - Informations complémentaires',
            {
                'fields': (
                    'role', 'wilaya', 'phone_number', 'profile_image',
                    'date_of_birth', 'school',
                )
            },
        ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('FATIN - Informations complémentaires', {'fields': ('email', 'role')}),
    )

    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        if obj.role == User.Role.STUDENT:
            return [StudentProfileInline]
        if obj.role == User.Role.TEACHER:
            return [TeacherProfileInline]
        return []


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'level', 'enrollment_date', 'parent_name', 'parent_phone')
    list_filter = ('level',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'parent_name')
    autocomplete_fields = ('user', 'level')


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'qualification', 'years_of_experience')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'subjects')
    autocomplete_fields = ('user',)
