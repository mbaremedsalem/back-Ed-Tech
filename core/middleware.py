"""
core/middleware.py
"""

import json
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from analytics.models import SystemLog
from users.models import User

class SecurityLoggingMiddleware(MiddlewareMixin):
    """Middleware لتسجيل أحداث الأمان"""
    
    def process_request(self, request):
        # تخطي طلبات static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None
        
        # تسجيل محاولات تسجيل الدخول الفاشلة
        if request.path == '/api/auth/login/' and request.method == 'POST':
            try:
                body = json.loads(request.body.decode('utf-8'))
                username = body.get('username', '')
                
                # التحقق من محاولات متكررة
                recent_failures = SystemLog.objects.filter(
                    message__contains=f'فشل تسجيل الدخول للمستخدم: {username}',
                    created_at__gte=timezone.now() - timezone.timedelta(minutes=15)
                ).count()
                
                if recent_failures >= 5:
                    SystemLog.objects.create(
                        level='security',
                        category='user',
                        message=f'محاولات تسجيل دخول مشبوهة للمستخدم: {username}',
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
            except:
                pass
        
        return None
    
    def process_response(self, request, response):
        # تسجيل الأنشطة المهمة
        if response.status_code == 401 or response.status_code == 403:
            SystemLog.objects.create(
                level='security',
                category='user',
                message=f'وصول غير مصرح للمسار: {request.path}',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                user=request.user if request.user.is_authenticated else None
            )
        
        # تسجيل عمليات الحذف المهمة
        if request.method == 'DELETE' and response.status_code == 204:
            SystemLog.objects.create(
                level='warning',
                category='system',
                message=f'تم حذف بيانات من المسار: {request.path}',
                ip_address=self.get_client_ip(request),
                user=request.user if request.user.is_authenticated else None
            )
        
        return response
    
    def process_exception(self, request, exception):
        # تسجيل الأخطاء الحرجة
        SystemLog.objects.create(
            level='error',
            category='system',
            message=f'خطأ في النظام: {str(exception)}',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            user=request.user if request.user.is_authenticated else None
        )
        return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class RoleBasedAccessMiddleware(MiddlewareMixin):
    """Middleware للتحقق من الصلاحيات حسب الدور"""
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # إذا لم يكن المستخدم مسجل دخول، تخطي التحقق
        if not request.user.is_authenticated:
            return None
        
        user_role = request.user.role
        path = request.path
        
        # تعريف قيود الوصول حسب الدور
        access_rules = self.get_access_rules(user_role)
        
        # التحقق من الوصول إلى المسار
        for rule_path, allowed_methods in access_rules.items():
            if path.startswith(rule_path) and request.method not in allowed_methods:
                from rest_framework.response import Response
                from rest_framework import status
                return Response(
                    {'error': 'غير مصرح لك بالوصول إلى هذا المورد'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return None
    
    def get_access_rules(self, role):
        """قواعد الوصول حسب الدور"""
        rules = {
            'student': {
                '/api/auth/': ['GET', 'POST', 'PUT', 'PATCH'],
                '/api/curriculum/units/': ['GET'],
                '/api/assessment/activities/': ['GET', 'POST'],
                '/api/assessment/attempts/': ['GET', 'POST'],
                '/api/assessment/progress/': ['GET'],
                '/api/analytics/learning/': ['GET'],
            },
            'teacher': {
                '/api/auth/': ['GET', 'POST', 'PUT', 'PATCH'],
                '/api/curriculum/': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
                '/api/assessment/': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
                '/api/analytics/': ['GET'],
                '/api/assessment/progress/': ['GET'],
            },
            'admin': {
                '/api/': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
                '/admin/': ['GET', 'POST'],
            }
        }
        
        return rules.get(role, {})