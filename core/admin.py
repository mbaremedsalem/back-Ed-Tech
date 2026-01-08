"""
core/admin.py - الإصدار المصحح
"""

from multiprocessing import context
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from users.models import User
from curriculum.models import Subject, Unit
from assessment.models import Activity, StudentProgress
from analytics.models import SystemLog

class EdTechAdminSite(AdminSite):
    site_header = 'إدارة منصة Ed-Tech التعليمية'
    site_title = 'لوحة تحكم Ed-Tech'
    index_title = 'مرحباً بك في لوحة إدارة المنصة التعليمية'

# إنشاء نسخة مخصصة من AdminSite
edtech_admin_site = EdTechAdminSite(name='edtech_admin')

# نموذج افتراضي للDashboard (يمكن حذفه إذا لم يكن بحاجة إليه)
class Dashboard:
    """فئة وهمية للداشبورد"""
    pass

# تسجيل النماذج مع النسخة المخصصة
from users.admin import CustomUserAdmin, TeacherProfileAdmin, StudentProfileAdmin
from curriculum.admin import SubjectAdmin, UnitAdmin, ContentSectionAdmin
from assessment.admin import ActivityAdmin, StudentAttemptAdmin, StudentProgressAdmin
from analytics.admin import LearningAnalyticsAdmin, TeacherDashboardAdmin, SystemLogAdmin

edtech_admin_site.register(User, CustomUserAdmin)
# ... سجل باقي النماذج هنا

class DashboardAdmin(admin.ModelAdmin):
    """لوحة تحكم مخصصة للرئيسية"""
    
    def has_module_permission(self, request):
        # إظهار فقط للمستخدمين الذين لديهم صلاحيات staff
        return request.user.is_staff
    
    def changelist_view(self, request, extra_context=None):
        # جمع إحصائيات النظام
        from django.db.models import Count, Avg, Sum
        
        stats = {
            'total_users': User.objects.count(),
            'total_students': User.objects.filter(role='student').count(),
            'total_teachers': User.objects.filter(role='teacher').count(),
            'total_subjects': Subject.objects.count(),
            'total_units': Unit.objects.count(),
            'total_activities': Activity.objects.count(),
            'total_attempts': StudentProgress.objects.count(),
        }
        
        # إحصائيات النشاط اليومي
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        daily_stats = {
            'new_users_today': User.objects.filter(date_joined__date=today).count(),
            'new_units_today': Unit.objects.filter(created_at__date=today).count(),
            'active_students_today': StudentProgress.objects.filter(
                last_accessed__date=today
            ).values('student').distinct().count(),
        }
        
        extra_context = extra_context or {}
        extra_context.update({
            'stats': stats,
            'daily_stats': daily_stats,
            'title': 'لوحة تحكم النظام التعليمي'
        })
        
        # استخدام template افتراضي
        from django.shortcuts import render
        return render(request, 'admin/dashboard.html', context)

# إضافة DashboardAdmin إلى AdminSite المخصص إذا كان بحاجة إليه
# edtech_admin_site.register(Dashboard, DashboardAdmin)