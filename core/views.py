"""
core/views.py
"""

from time import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
from assessment.models import Activity
from curriculum.models import Unit
import redis
import psycopg2

class HealthCheckView(APIView):
    permission_classes = []  # بدون مصادقة
    
    def get(self, request):
        """فحص صحة النظام"""
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'services': {}
        }
        
        # فحص قاعدة البيانات
        try:
            connection.ensure_connection()
            health_status['services']['database'] = {
                'status': 'healthy',
                'type': 'PostgreSQL'
            }
        except Exception as e:
            health_status['services']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        # فحص الكاش (إذا كان مستخدماً)
        try:
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                health_status['services']['cache'] = {
                    'status': 'healthy'
                }
        except Exception as e:
            health_status['services']['cache'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        # إحصائيات النظام
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            health_status['statistics'] = {
                'total_users': User.objects.count(),
                'total_units': Unit.objects.count() if 'Unit' in globals() else 0,
                'total_activities': Activity.objects.count() if 'Activity' in globals() else 0,
                'system_uptime': self.get_system_uptime()
            }
        except Exception as e:
            health_status['statistics'] = {
                'error': f'فشل في جمع الإحصائيات: {str(e)}'
            }
        
        # إرجاع الاستجابة مع الكود المناسب
        if health_status['status'] == 'healthy':
            return Response(health_status, status=status.HTTP_200_OK)
        else:
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    def get_system_uptime(self):
        """الحصول على مدة تشغيل النظام (بشكل مبسط)"""
        import subprocess
        try:
            # لنظام Linux
            result = subprocess.run(['uptime', '-p'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return 'غير متاح'