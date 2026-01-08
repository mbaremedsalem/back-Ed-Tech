"""
analytics/views.py - تحديث الـ Views لتعمل مع path
"""

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# from core import models
from .models import LearningAnalytics, TeacherDashboard, SystemLog
from users.models import User
from curriculum.models import Unit, Subject
from assessment.models import StudentProgress, StudentAttempt
from .serializers import (
    LearningAnalyticsSerializer,
    TeacherDashboardSerializer,
    SystemLogSerializer,
    AnalyticsReportSerializer
)

# Learning Analytics Views
class LearningAnalyticsListView(generics.ListAPIView):
    serializer_class = LearningAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'student':
            return LearningAnalytics.objects.filter(student=user)
        elif user.role == 'teacher':
            teacher_units = Unit.objects.filter(created_by=user)
            student_progress = StudentProgress.objects.filter(unit__in=teacher_units)
            student_ids = student_progress.values_list('student_id', flat=True)
            return LearningAnalytics.objects.filter(student_id__in=student_ids)
        elif user.role == 'admin':
            return LearningAnalytics.objects.all()
        
        return LearningAnalytics.objects.none()
    
    def get(self, request):
        analytics = self.get_queryset()
        serializer = self.get_serializer(analytics, many=True)
        return Response(serializer.data)

class DailyLearningReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        date_param = request.query_params.get('date', None)
        
        if date_param:
            try:
                target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'صيغة التاريخ غير صحيحة. استخدم YYYY-MM-DD'}, status=400)
        else:
            target_date = timezone.now().date()
        
        if user.role == 'student':
            report = self.get_student_daily_report(user, target_date)
        elif user.role == 'teacher':
            report = self.get_teacher_daily_report(user, target_date)
        elif user.role == 'admin':
            report = self.get_admin_daily_report(target_date)
        else:
            return Response({'error': 'غير مصرح'}, status=403)
        
        return Response(report)
    
    def get_student_daily_report(self, user, date):
        """تقرير يومي للطالب"""
        daily_attempts = StudentAttempt.objects.filter(
            student=user,
            attempted_at__date=date
        )
        
        total_attempts = daily_attempts.count()
        correct_attempts = daily_attempts.filter(is_correct=True).count()
        
        report = {
            'date': date,
            'student': user.get_full_name(),
            'total_activities': total_attempts,
            'correct_activities': correct_attempts,
            'success_rate': (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            'total_score': daily_attempts.aggregate(Sum('score'))['score__sum'] or 0,
            'average_time_per_activity': daily_attempts.aggregate(Avg('time_taken'))['time_taken__avg'] or 0,
            'activities_by_type': daily_attempts.values('activity__activity_type').annotate(
                count=Count('id'),
                avg_score=Avg('score')
            ),
            'units_accessed': daily_attempts.values('activity__unit__title').distinct().count()
        }
        
        return report
    
    def get_teacher_daily_report(self, teacher, date):
        """تقرير يومي للمعلم"""
        teacher_units = Unit.objects.filter(created_by=teacher)
        
        daily_attempts = StudentAttempt.objects.filter(
            activity__unit__in=teacher_units,
            attempted_at__date=date
        )
        
        unique_students = daily_attempts.values('student').distinct().count()
        
        report = {
            'date': date,
            'teacher': teacher.get_full_name(),
            'total_activities_submitted': daily_attempts.count(),
            'unique_students_active': unique_students,
            'overall_success_rate': self.calculate_success_rate(daily_attempts),
            'units_activity': daily_attempts.values('activity__unit__title').annotate(
                count=Count('id'),
                avg_score=Avg('score')
            ),
            'top_performing_students': daily_attempts.values(
                'student__username', 'student__first_name', 'student__last_name'
            ).annotate(
                total_score=Sum('score'),
                activities_count=Count('id')
            ).order_by('-total_score')[:5]
        }
        
        return report
    
    def get_admin_daily_report(self, date):
        """تقرير يومي للمدير"""
        daily_attempts = StudentAttempt.objects.filter(attempted_at__date=date)
        
        report = {
            'date': date,
            'total_activities': daily_attempts.count(),
            'active_students': daily_attempts.values('student').distinct().count(),
            'active_teachers': User.objects.filter(
                role='teacher',
                last_login__date=date
            ).count(),
            'overall_success_rate': self.calculate_success_rate(daily_attempts),
            'system_usage_by_hour': self.get_usage_by_hour(date),
            'new_users': User.objects.filter(date_joined__date=date).count()
        }
        
        return report
    
    def calculate_success_rate(self, attempts_queryset):
        """حساب معدل النجاح"""
        total = attempts_queryset.count()
        if total == 0:
            return 0
        
        correct = attempts_queryset.filter(is_correct=True).count()
        return (correct / total) * 100
    
    def get_usage_by_hour(self, date):
        """الحصول على استخدام النظام حسب الساعة"""
        from django.db.models.functions import ExtractHour
        
        usage = StudentAttempt.objects.filter(
            attempted_at__date=date
        ).annotate(
            hour=ExtractHour('attempted_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')
        
        return list(usage)

class StudentLearningAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, student_id):
        try:
            student = User.objects.get(pk=student_id, role='student')
        except User.DoesNotExist:
            return Response({'error': 'الطالب غير موجود'}, status=404)
        
        user = request.user
        
        # التحقق من الصلاحيات
        if user.role == 'student' and user.id != student_id:
            return Response({'error': 'غير مصرح بالوصول'}, status=403)
        elif user.role == 'teacher':
            # التحقق إذا كان الطالب يدرس لدى هذا المعلم
            teacher_units = Unit.objects.filter(created_by=user)
            student_progress = StudentProgress.objects.filter(
                student=student,
                unit__in=teacher_units
            )
            if not student_progress.exists():
                return Response({'error': 'غير مصرح بالوصول'}, status=403)
        
        # جمع البيانات التحليلية
        analytics_data = {
            'student_info': {
                'id': student.id,
                'name': student.get_full_name(),
                'grade': student.grade,
                'school': student.school
            },
            'overall_progress': self.get_overall_progress(student),
            'recent_activity': self.get_recent_activity(student),
            'strengths_weaknesses': self.get_strengths_weaknesses(student),
            'learning_trends': self.get_learning_trends(student)
        }
        
        return Response(analytics_data)
    
    def get_overall_progress(self, student):
        """الحصول على التقدم العام"""
        progress = StudentProgress.objects.filter(student=student)
        
        return {
            'total_units': progress.count(),
            'completed_units': progress.filter(completion_percentage=100).count(),
            'average_progress': progress.aggregate(Avg('completion_percentage'))['completion_percentage__avg'] or 0,
            'total_score': progress.aggregate(Sum('total_score'))['total_score__sum'] or 0,
            'mastery_levels': progress.values('mastery_level').annotate(count=Count('id'))
        }
    
    def get_recent_activity(self, student, days=7):
        """الحصول على النشاط الأخير"""
        since_date = timezone.now() - timedelta(days=days)
        
        recent_attempts = StudentAttempt.objects.filter(
            student=student,
            attempted_at__gte=since_date
        )
        
        return {
            'days_analyzed': days,
            'total_attempts': recent_attempts.count(),
            'daily_average': recent_attempts.count() / days if days > 0 else 0,
            'success_rate': self.calculate_success_rate(recent_attempts),
            'most_active_day': self.get_most_active_day(recent_attempts)
        }
    
    def get_strengths_weaknesses(self, student):
        """الحصول على نقاط القوة والضعف"""
        attempts = StudentAttempt.objects.filter(student=student)
        
        # تحليل حسب نوع النشاط
        by_activity_type = attempts.values('activity__activity_type').annotate(
            total=Count('id'),
            correct=Count('id', filter=Q(is_correct=True)),
            avg_score=Avg('score')
        ).order_by('-avg_score')
        
        strengths = []
        weaknesses = []
        
        for item in by_activity_type:
            success_rate = (item['correct'] / item['total'] * 100) if item['total'] > 0 else 0
            
            if success_rate >= 70:
                strengths.append({
                    'activity_type': item['activity__activity_type'],
                    'success_rate': success_rate,
                    'attempts': item['total']
                })
            elif success_rate <= 40:
                weaknesses.append({
                    'activity_type': item['activity__activity_type'],
                    'success_rate': success_rate,
                    'attempts': item['total']
                })
        
        return {
            'strengths': strengths,
            'weaknesses': weaknesses
        }
    
    def get_learning_trends(self, student):
        """الحصول على اتجاهات التعلم"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        daily_progress = []
        for i in range(30):
            date = (timezone.now() - timedelta(days=i)).date()
            
            attempts = StudentAttempt.objects.filter(
                student=student,
                attempted_at__date=date
            )
            
            daily_progress.append({
                'date': date,
                'attempts': attempts.count(),
                'score': attempts.aggregate(Sum('score'))['score__sum'] or 0,
                'success_rate': self.calculate_success_rate(attempts)
            })
        
        # عكس القائمة لتكون من الأقدم إلى الأحدث
        daily_progress.reverse()
        
        return {
            'period_days': 30,
            'daily_progress': daily_progress,
            'improvement_rate': self.calculate_improvement_rate(daily_progress)
        }
    
    def calculate_success_rate(self, attempts_queryset):
        """حساب معدل النجاح"""
        total = attempts_queryset.count()
        if total == 0:
            return 0
        
        correct = attempts_queryset.filter(is_correct=True).count()
        return (correct / total) * 100
    
    def get_most_active_day(self, attempts_queryset):
        """الحصول على اليوم الأكثر نشاطاً"""
        from django.db.models.functions import TruncDay
        
        active_days = attempts_queryset.annotate(
            day=TruncDay('attempted_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        return active_days
    
    def calculate_improvement_rate(self, daily_progress):
        """حساب معدل التحسن"""
        if len(daily_progress) < 2:
            return 0
        
        first_week_avg = sum(item['success_rate'] for item in daily_progress[:7]) / 7
        last_week_avg = sum(item['success_rate'] for item in daily_progress[-7:]) / 7
        
        if first_week_avg > 0:
            return ((last_week_avg - first_week_avg) / first_week_avg) * 100
        
        return last_week_avg * 100

# Teacher Dashboard Views
class TeacherDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.role not in ['teacher', 'admin']:
            return Response({'error': 'غير مصرح'}, status=403)
        
        teacher = request.user
        
        # الحصول على أو إنشاء لوحة التحكم
        dashboard, created = TeacherDashboard.objects.get_or_create(
            teacher=teacher,
            defaults={
                'total_students': 0,
                'active_students': 0,
                'total_units_created': 0,
                'student_engagement_rate': 0,
                'avg_student_progress': 0
            }
        )
        
        # تحديث البيانات
        self.update_dashboard_data(dashboard)
        
        serializer = TeacherDashboardSerializer(dashboard)
        return Response(serializer.data)
    
    def update_dashboard_data(self, dashboard):
        """تحديث بيانات لوحة التحكم"""
        teacher = dashboard.teacher
        teacher_units = Unit.objects.filter(created_by=teacher)
        
        # طلاب درسوا وحدات المعلم
        student_progress = StudentProgress.objects.filter(unit__in=teacher_units)
        unique_students = student_progress.values('student').distinct().count()
        
        # الطلاب النشطين في آخر 7 أيام
        last_week = timezone.now() - timedelta(days=7)
        active_students = student_progress.filter(
            last_accessed__gte=last_week
        ).values('student').distinct().count()
        
        # معدل التفاعل
        engagement_rate = self.calculate_engagement_rate(teacher)
        
        # متوسط تقدم الطلاب
        avg_progress = student_progress.aggregate(
            avg=Avg('completion_percentage')
        )['avg'] or 0
        
        # تحديث لوحة التحكم
        dashboard.total_students = unique_students
        dashboard.active_students = active_students
        dashboard.total_units_created = teacher_units.count()
        dashboard.student_engagement_rate = engagement_rate
        dashboard.avg_student_progress = avg_progress
        dashboard.save()
    
    def calculate_engagement_rate(self, teacher):
        """حساب معدل تفاعل الطلاب"""
        teacher_units = Unit.objects.filter(created_by=teacher)
        
        if not teacher_units.exists():
            return 0
        
        total_activities = sum(unit.activities.count() for unit in teacher_units)
        total_attempts = StudentAttempt.objects.filter(
            activity__unit__in=teacher_units
        ).count()
        
        if total_activities > 0:
            return (total_attempts / total_activities) * 100
        return 0

class TeacherDashboardOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.role not in ['teacher', 'admin']:
            return Response({'error': 'غير مصرح'}, status=403)
        
        teacher = request.user
        
        overview = {
            'teacher_info': {
                'name': teacher.get_full_name(),
                'subjects': teacher.teacher_profile.subjects if hasattr(teacher, 'teacher_profile') else '',
                'experience': teacher.teacher_profile.years_of_experience if hasattr(teacher, 'teacher_profile') else 0
            },
            'quick_stats': self.get_quick_stats(teacher),
            'recent_activity': self.get_recent_activity(teacher),
            'upcoming_deadlines': self.get_upcoming_deadlines(teacher),
            'notifications': self.get_notifications(teacher)
        }
        
        return Response(overview)
    
    def get_quick_stats(self, teacher):
        """الحصول على إحصائيات سريعة"""
        teacher_units = Unit.objects.filter(created_by=teacher)
        
        student_progress = StudentProgress.objects.filter(unit__in=teacher_units)
        unique_students = student_progress.values('student').distinct().count()
        
        return {
            'total_students': unique_students,
            'total_units': teacher_units.count(),
            'published_units': teacher_units.filter(is_published=True).count(),
            'total_activities': sum(unit.activities.count() for unit in teacher_units),
            'avg_student_progress': student_progress.aggregate(
                avg=Avg('completion_percentage')
            )['avg'] or 0
        }
    
    def get_recent_activity(self, teacher):
        """الحصول على النشاط الأخير"""
        last_24_hours = timezone.now() - timedelta(hours=24)
        
        teacher_units = Unit.objects.filter(created_by=teacher)
        
        recent_attempts = StudentAttempt.objects.filter(
            activity__unit__in=teacher_units,
            attempted_at__gte=last_24_hours
        )
        
        return {
            'period': '24 ساعة',
            'total_attempts': recent_attempts.count(),
            'unique_students': recent_attempts.values('student').distinct().count(),
            'top_activities': recent_attempts.values('activity__title').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
        }
    
    def get_upcoming_deadlines(self, teacher):
        """الحصول على المواعيد النهائية القادمة"""
        # هذه دالة افتراضية، يمكن توسيعها حسب الحاجة
        return [
            {
                'title': 'مراجعة الوحدة الأولى',
                'deadline': (timezone.now() + timedelta(days=3)).date(),
                'priority': 'high'
            },
            {
                'title': 'تصحيح الأنشطة',
                'deadline': (timezone.now() + timedelta(days=1)).date(),
                'priority': 'medium'
            }
        ]
    
    def get_notifications(self, teacher):
        """الحصول على الإشعارات"""
        teacher_units = Unit.objects.filter(created_by=teacher)
        
        # طلاب يحتاجون إلى دعم
        struggling_students = StudentProgress.objects.filter(
            unit__in=teacher_units,
            completion_percentage__lt=30
        ).values('student__username', 'student__first_name', 'unit__title').distinct()[:5]
        
        # وحدات بحاجة إلى تحديث
        old_units = teacher_units.filter(
            updated_at__lte=timezone.now() - timedelta(days=90)
        )[:3]
        
        return {
            'struggling_students': list(struggling_students),
            'old_units': [
                {
                    'title': unit.title,
                    'last_updated': unit.updated_at.date(),
                    'days_since_update': (timezone.now().date() - unit.updated_at.date()).days
                }
                for unit in old_units
            ]
        }

class TeacherStudentsProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.role not in ['teacher', 'admin']:
            return Response({'error': 'غير مصرح'}, status=403)
        
        teacher = request.user
        
        students_progress = self.get_students_progress(teacher)
        
        return Response({
            'teacher': teacher.get_full_name(),
            'total_students': len(students_progress),
            'students_progress': students_progress
        })
    
    def get_students_progress(self, teacher):
        """الحصول على تقدم جميع طلاب المعلم"""
        teacher_units = Unit.objects.filter(created_by=teacher)
        
        # الحصول على جميع الطلاب الذين درسوا وحدات المعلم
        student_progress = StudentProgress.objects.filter(
            unit__in=teacher_units
        ).select_related('student', 'unit')
        
        # تجميع البيانات حسب الطالب
        students_data = {}
        
        for progress in student_progress:
            student_id = progress.student.id
            
            if student_id not in students_data:
                students_data[student_id] = {
                    'student_info': {
                        'id': progress.student.id,
                        'name': progress.student.get_full_name(),
                        'username': progress.student.username,
                        'grade': progress.student.grade
                    },
                    'units_progress': [],
                    'total_score': 0,
                    'average_progress': 0,
                    'units_count': 0
                }
            
            students_data[student_id]['units_progress'].append({
                'unit_id': progress.unit.id,
                'unit_title': progress.unit.title,
                'progress_percentage': progress.completion_percentage,
                'mastery_level': progress.mastery_level,
                'score': progress.total_score,
                'last_accessed': progress.last_accessed
            })
            
            students_data[student_id]['total_score'] += progress.total_score
            students_data[student_id]['units_count'] += 1
        
        # حساب المتوسطات
        for student_id in students_data:
            units_count = students_data[student_id]['units_count']
            if units_count > 0:
                total_progress = sum(
                    unit['progress_percentage'] 
                    for unit in students_data[student_id]['units_progress']
                )
                students_data[student_id]['average_progress'] = total_progress / units_count
        
        # تحويل القاموس إلى قائمة
        return list(students_data.values())

class TeacherUnitsPerformanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.role not in ['teacher', 'admin']:
            return Response({'error': 'غير مصرح'}, status=403)
        
        teacher = request.user
        
        units_performance = self.get_units_performance(teacher)
        
        return Response({
            'teacher': teacher.get_full_name(),
            'total_units': len(units_performance),
            'units_performance': units_performance
        })
    
    def get_units_performance(self, teacher):
        """الحصول على أداء وحدات المعلم"""
        teacher_units = Unit.objects.filter(created_by=teacher)
        
        units_data = []
        
        for unit in teacher_units:
            student_progress = StudentProgress.objects.filter(unit=unit)
            
            if student_progress.exists():
                avg_progress = student_progress.aggregate(
                    avg=Avg('completion_percentage')
                )['avg'] or 0
                
                avg_score = student_progress.aggregate(
                    avg=Avg('total_score')
                )['avg'] or 0
                
                students_count = student_progress.count()
                completed_count = student_progress.filter(completion_percentage=100).count()
                
                units_data.append({
                    'unit_id': unit.id,
                    'unit_title': unit.title,
                    'subject': unit.subject.name,
                    'difficulty': unit.difficulty,
                    'is_published': unit.is_published,
                    'created_at': unit.created_at.date(),
                    'students_count': students_count,
                    'completed_count': completed_count,
                    'completion_rate': (completed_count / students_count * 100) if students_count > 0 else 0,
                    'average_progress': avg_progress,
                    'average_score': avg_score,
                    'total_activities': unit.activities.count(),
                    'total_attempts': StudentAttempt.objects.filter(activity__unit=unit).count()
                })
        
        # ترتيب حسب نسبة الإنجاز
        units_data.sort(key=lambda x: x['completion_rate'], reverse=True)
        
        return units_data

# System Logs Views
class SystemLogListView(generics.ListAPIView):
    serializer_class = SystemLogSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = SystemLog.objects.all()
        
        # تطبيق الفلاتر
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__range=[start_date, end_date]
            )
        
        return queryset.order_by('-created_at')
    
    def get(self, request):
        logs = self.get_queryset()
        
        # تحديد الحد الأقصى
        limit = int(request.query_params.get('limit', 100))
        logs = logs[:limit]
        
        serializer = self.get_serializer(logs, many=True)
        
        # إضافة إحصائيات
        stats = {
            'total_logs': logs.count(),
            'levels_distribution': logs.values('level').annotate(count=Count('id')),
            'categories_distribution': logs.values('category').annotate(count=Count('id'))
        }
        
        return Response({
            'logs': serializer.data,
            'statistics': stats,
            'limit': limit
        })

class SecurityReportView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        security_logs = SystemLog.objects.filter(
            level='security',
            created_at__gte=thirty_days_ago
        )
        
        # تحليل محاولات تسجيل الدخول الفاشلة
        failed_logins = security_logs.filter(
            message__icontains='فشل تسجيل الدخول'
        )
        
        # تحليل الأنشطة المشبوهة
        suspicious_activities = security_logs.filter(
            Q(message__icontains='مشبوه') | 
            Q(message__icontains='غير مصرح') |
            Q(message__icontains='محاولة وصول')
        )
        
        report = {
            'period': 'آخر 30 يوم',
            'total_security_events': security_logs.count(),
            'failed_login_attempts': {
                'total': failed_logins.count(),
                'by_user': failed_logins.values('user__username').annotate(
                    count=Count('id')
                ).order_by('-count')[:10],
                'by_ip': failed_logins.values('ip_address').annotate(
                    count=Count('id')
                ).order_by('-count')[:10]
            },
            'suspicious_activities': {
                'total': suspicious_activities.count(),
                'by_category': suspicious_activities.values('category').annotate(
                    count=Count('id')
                ),
                'recent_activities': SystemLogSerializer(
                    suspicious_activities.order_by('-created_at')[:20],
                    many=True
                ).data
            },
            'recommendations': self.generate_security_recommendations(security_logs)
        }
        
        return Response(report)
    
    def generate_security_recommendations(self, security_logs):
        """إنشاء توصيات أمنية"""
        recommendations = []
        
        # تحليل محاولات تسجيل الدخول الفاشلة
        failed_logins = security_logs.filter(
            message__icontains='فشل تسجيل الدخول'
        )
        
        if failed_logins.count() > 100:
            recommendations.append({
                'priority': 'high',
                'title': 'زيادة محاولات تسجيل الدخول الفاشلة',
                'description': 'تم اكتشاف أكثر من 100 محاولة تسجيل دخول فاشلة في الشهر الماضي',
                'action': 'تفعيل تأكيد الهوية الثنائية للمستخدمين المهمين'
            })
        
        # تحليل IPs مشبوهة
        suspicious_ips = failed_logins.values('ip_address').annotate(
            count=Count('id')
        ).filter(count__gte=10)
        
        if suspicious_ips.exists():
            recommendations.append({
                'priority': 'medium',
                'title': 'عناوين IP مشبوهة',
                'description': f'تم اكتشاف {suspicious_ips.count()} عنوان IP يقوم بمحاولات تسجيل دخول متكررة',
                'action': 'حظر عناوين IP المدرجة في القائمة السوداء'
            })
        
        # تحليل سجلات الأخطاء
        error_logs = SystemLog.objects.filter(
            level='error',
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        if error_logs.count() > 50:
            recommendations.append({
                'priority': 'low',
                'title': 'زيادة في أخطاء النظام',
                'description': 'تم تسجيل أكثر من 50 خطأ في الشهر الماضي',
                'action': 'مراجعة سجلات الأخطاء وإصلاح المشاكل الأساسية'
            })
        
        return recommendations

class ErrorLogsView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        error_logs = SystemLog.objects.filter(
            level='error',
            created_at__gte=thirty_days_ago
        )
        
        # تحليل الأخطاء
        error_analysis = {
            'total_errors': error_logs.count(),
            'errors_by_category': error_logs.values('category').annotate(
                count=Count('id')
            ).order_by('-count'),
            'frequent_errors': error_logs.values('message').annotate(
                count=Count('id')
            ).order_by('-count')[:10],
            'errors_timeline': self.get_errors_timeline(error_logs),
            'recent_errors': SystemLogSerializer(
                error_logs.order_by('-created_at')[:20],
                many=True
            ).data
        }
        
        return Response(error_analysis)
    
    def get_errors_timeline(self, error_logs):
        """الحصول على خط زمني للأخطاء"""
        timeline = []
        
        for i in range(30, -1, -1):
            date = (timezone.now() - timedelta(days=i)).date()
            
            daily_errors = error_logs.filter(created_at__date=date)
            
            timeline.append({
                'date': date,
                'count': daily_errors.count(),
                'categories': daily_errors.values('category').annotate(
                    count=Count('id')
                )
            })
        
        return timeline

from datetime import timedelta
from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.db.models import Avg, Count, Sum
from django.db import models 
from django.db.models.functions import ExtractHour, ExtractMonth, ExtractYear

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from users.models import User

from curriculum.models import Subject

from .serializers import AnalyticsReportSerializer


class AnalyticsReportAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        """تقرير تحليلات شامل للمدير"""

        report = {
            'usage_analytics': self.get_usage_analytics(),
            'performance_analytics': self.get_performance_analytics(),
            'user_analytics': self.get_user_analytics(),
            'content_analytics': self.get_content_analytics(),
            'generated_at': timezone.now()
        }

        serializer = AnalyticsReportSerializer(report)
        return Response(serializer.data)

    # ==========================
    # USAGE ANALYTICS
    # ==========================
    def get_usage_analytics(self):
        thirty_days_ago = timezone.now() - timedelta(days=30)

        return {
            'total_logins': User.objects.filter(
                last_login__gte=thirty_days_ago
            ).count(),
            'daily_active_users': self.calculate_dau(),
            'total_activities_completed': StudentAttempt.objects.filter(
                attempted_at__gte=thirty_days_ago
            ).count(),
            'avg_session_duration': self.calculate_avg_session_duration(),
            'peak_usage_hours': self.get_peak_usage_hours()
        }

    def calculate_dau(self):
        today = timezone.now().date()
        return User.objects.filter(last_login__date=today).count()

    def calculate_avg_session_duration(self):
        return (
            StudentAttempt.objects.aggregate(
                avg=Avg('time_taken')
            )['avg'] or 0
        )

    def get_peak_usage_hours(self):
        return list(
            StudentAttempt.objects.annotate(
                hour=ExtractHour('attempted_at')
            ).values('hour').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
        )

    # ==========================
    # PERFORMANCE ANALYTICS
    # ==========================
    def get_performance_analytics(self):
        return {
            'overall_success_rate': self.calculate_overall_success_rate(),
            'avg_completion_rate': StudentProgress.objects.aggregate(
                avg=Avg('completion_percentage')
            )['avg'] or 0,
            'top_performing_students': self.get_top_performers(),
            'struggling_students': self.get_struggling_students(),
            'subject_performance': self.get_subject_performance()
        }

    def calculate_overall_success_rate(self):
        total_attempts = StudentAttempt.objects.count()
        if total_attempts == 0:
            return 0

        correct_attempts = StudentAttempt.objects.filter(is_correct=True).count()
        return round((correct_attempts / total_attempts) * 100, 2)

    def get_top_performers(self, limit=10):
        return list(
            StudentProgress.objects.values(
                'student__username',
                'student__first_name',
                'student__last_name'
            ).annotate(
                avg_progress=Avg('completion_percentage'),
                total_score=Sum('total_score')
            ).order_by('-avg_progress')[:limit]
        )

    def get_struggling_students(self, threshold=30):
        return list(
            StudentProgress.objects.values(
                'student__username',
                'student__first_name',
                'student__last_name'
            ).annotate(
                avg_progress=Avg('completion_percentage')
            ).filter(avg_progress__lt=threshold)[:10]
        )

    def get_subject_performance(self):
        return list(
            Subject.objects.annotate(
                avg_progress=Avg('units__student_progress__completion_percentage'),
                total_students=Count(
                    'units__student_progress__student',
                    distinct=True
                )
            ).values(
                'name',
                'grade',
                'avg_progress',
                'total_students'
            )
        )

    # ==========================
    # USER ANALYTICS
    # ==========================
    def get_user_analytics(self):
        thirty_days_ago = timezone.now() - timedelta(days=30)

        return {
            'total_users': User.objects.count(),
            'role_distribution': list(
                User.objects.values('role').annotate(count=Count('id'))
            ),
            'new_users_last_30_days': User.objects.filter(
                date_joined__gte=thirty_days_ago
            ).count(),
            'active_users_rate': self.calculate_active_users_rate(),
            'user_growth': self.calculate_user_growth()
        }

    def calculate_active_users_rate(self):
        thirty_days_ago = timezone.now() - timedelta(days=30)

        total_users = User.objects.count()
        if total_users == 0:
            return 0

        active_users = User.objects.filter(
            last_login__gte=thirty_days_ago
        ).count()

        return round((active_users / total_users) * 100, 2)

    def calculate_user_growth(self):
        now = timezone.now()
        last_month = now - relativedelta(months=1)

        current_month_users = User.objects.filter(
            date_joined__year=now.year,
            date_joined__month=now.month
        ).count()

        last_month_users = User.objects.filter(
            date_joined__year=last_month.year,
            date_joined__month=last_month.month
        ).count()

        growth_rate = (
            ((current_month_users - last_month_users) / last_month_users) * 100
            if last_month_users > 0 else 100
        )

        return {
            'current_month': current_month_users,
            'last_month': last_month_users,
            'growth_rate': round(growth_rate, 2)
        }

    # ==========================
    # CONTENT ANALYTICS
    # ==========================
    def get_content_analytics(self):
        return {
            'total_units': Unit.objects.count(),
            'published_units': Unit.objects.filter(is_published=True).count(),
            'units_by_difficulty': list(
                Unit.objects.values('difficulty').annotate(count=Count('id'))
            ),
            'most_accessed_units': list(
                Unit.objects.annotate(
                    access_count=Count('student_progress')
                ).order_by('-access_count')[:10].values(
                    'id',
                    'title',
                    'difficulty',
                    'access_count'
                )
            ),
            'content_creation_trend': self.get_content_creation_trend()
        }

    def get_content_creation_trend(self):
        six_months_ago = timezone.now() - relativedelta(months=6)

        return list(
            Unit.objects.filter(
                created_at__gte=six_months_ago
            ).annotate(
                year=ExtractYear('created_at'),
                month=ExtractMonth('created_at')
            ).values(
                'year',
                'month'
            ).annotate(
                count=Count('id')
            ).order_by('year', 'month')
        )

class UsageAnalyticsView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """تحليل استخدام النظام"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        usage_data = {
            'total_logins': User.objects.filter(
                last_login__gte=thirty_days_ago
            ).count(),
            'daily_active_users': self.calculate_dau(),
            'total_activities_completed': StudentAttempt.objects.filter(
                attempted_at__gte=thirty_days_ago
            ).count(),
            'avg_session_duration': self.calculate_avg_session_duration(),
            'peak_usage_hours': self.get_peak_usage_hours(),
            'usage_trend': self.get_usage_trend()
        }
        
        return Response(usage_data)
    
    def calculate_dau(self):
        """حساب المستخدمين النشطين يومياً"""
        today = timezone.now().date()
        return User.objects.filter(
            last_login__date=today
        ).count()
    
    def calculate_avg_session_duration(self):
        """حساب متوسط مدة الجلسة"""
        attempts = StudentAttempt.objects.all()
        if attempts.exists():
            return attempts.aggregate(Avg('time_taken'))['time_taken__avg']
        return 0
    
    def get_peak_usage_hours(self):
        """الحصول على ساعات الذروة في الاستخدام"""
        from django.db.models.functions import ExtractHour
        
        usage_by_hour = StudentAttempt.objects.annotate(
            hour=ExtractHour('attempted_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return list(usage_by_hour)
    
    def get_usage_trend(self):
        """الحصول على اتجاه الاستخدام"""
        trend = []
        
        for i in range(30, -1, -1):
            date = (timezone.now() - timedelta(days=i)).date()
            
            daily_attempts = StudentAttempt.objects.filter(
                attempted_at__date=date
            )
            
            trend.append({
                'date': date,
                'attempts': daily_attempts.count(),
                'unique_users': daily_attempts.values('student').distinct().count()
            })
        
        return trend

class PerformanceAnalyticsView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """تحليل أداء الطلاب"""
        performance_data = {
            'overall_success_rate': self.calculate_overall_success_rate(),
            'avg_completion_rate': StudentProgress.objects.aggregate(
                Avg('completion_percentage')
            )['completion_percentage__avg'] or 0,
            'top_performing_students': self.get_top_performers(),
            'struggling_students': self.get_struggling_students(),
            'subject_performance': self.get_subject_performance(),
            'difficulty_analysis': self.get_difficulty_analysis()
        }
        
        return Response(performance_data)
    
    def calculate_overall_success_rate(self):
        """حساب معدل النجاح الإجمالي"""
        total_attempts = StudentAttempt.objects.count()
        correct_attempts = StudentAttempt.objects.filter(is_correct=True).count()
        
        if total_attempts > 0:
            return (correct_attempts / total_attempts) * 100
        return 0
    
    def get_top_performers(self, limit=10):
        """الحصول على أفضل الأداء"""
        return StudentProgress.objects.values(
            'student__username', 'student__first_name', 'student__last_name'
        ).annotate(
            avg_progress=Avg('completion_percentage'),
            total_score=Sum('total_score')
        ).order_by('-avg_progress')[:limit]
    
    def get_struggling_students(self, threshold=30):
        """الحصول على الطلاب الذين يعانون"""
        return StudentProgress.objects.values(
            'student__username', 'student__first_name', 'student__last_name'
        ).annotate(
            avg_progress=Avg('completion_percentage')
        ).filter(avg_progress__lt=threshold)[:10]
    
    def get_subject_performance(self):
        """أداء الطلاب حسب المادة"""
        return Subject.objects.annotate(
            avg_progress=Avg('units__student_progress__completion_percentage'),
            total_students=Count('units__student_progress__student', distinct=True)
        ).values('name', 'grade', 'avg_progress', 'total_students')
    
    def get_difficulty_analysis(self):
        """تحليل الأداء حسب مستوى الصعوبة"""
        from curriculum.models import Unit
        
        return Unit.objects.values('difficulty').annotate(
            avg_progress=Avg('student_progress__completion_percentage'),
            total_students=Count('student_progress__student', distinct=True),
            success_rate=Avg('student_progress__completed_activities__attempts__is_correct')
        ).order_by('difficulty')

class UserAnalyticsView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """تحليل بيانات المستخدمين"""
        total_users = User.objects.count()
        
        user_data = {
            'total_users': total_users,
            'role_distribution': User.objects.values('role').annotate(count=Count('id')),
            'new_users_last_30_days': User.objects.filter(
                date_joined__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'active_users_rate': self.calculate_active_users_rate(),
            'user_growth': self.calculate_user_growth(),
            'retention_rate': self.calculate_retention_rate(),
            'user_engagement': self.get_user_engagement()
        }
        
        return Response(user_data)
    
    def calculate_active_users_rate(self):
        """حساب نسبة المستخدمين النشطين"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        total_users = User.objects.count()
        active_users = User.objects.filter(last_login__gte=thirty_days_ago).count()
        
        if total_users > 0:
            return (active_users / total_users) * 100
        return 0
    
    def calculate_user_growth(self):
        """حساب نمو المستخدمين"""
        now = timezone.now()
        last_month = now - relativedelta(months=1)
        two_months_ago = now - relativedelta(months=2)
        
        current_month_users = User.objects.filter(
            date_joined__month=now.month,
            date_joined__year=now.year
        ).count()
        
        last_month_users = User.objects.filter(
            date_joined__month=last_month.month,
            date_joined__year=last_month.year
        ).count()
        
        if last_month_users > 0:
            growth_rate = ((current_month_users - last_month_users) / last_month_users) * 100
        else:
            growth_rate = current_month_users * 100
        
        return {
            'current_month': current_month_users,
            'last_month': last_month_users,
            'growth_rate': growth_rate
        }
    
    def calculate_retention_rate(self):
        """حساب معدل الاحتفاظ بالمستخدمين"""
        # مستخدمين جدد منذ شهرين
        two_months_ago = timezone.now() - relativedelta(months=2)
        one_month_ago = timezone.now() - relativedelta(months=1)
        
        new_users_two_months_ago = User.objects.filter(
            date_joined__range=[two_months_ago, one_month_ago]
        ).count()
        
        if new_users_two_months_ago == 0:
            return 0
        
        # مستخدمين لا يزالون نشطين
        still_active = User.objects.filter(
            date_joined__range=[two_months_ago, one_month_ago],
            last_login__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return (still_active / new_users_two_months_ago) * 100
    
    def get_user_engagement(self):
        """الحصول على بيانات تفاعل المستخدمين"""
        user_engagement = []
        
        # تحليل حسب الدور
        for role in ['student', 'teacher', 'admin']:
            users = User.objects.filter(role=role)
            
            if users.exists():
                avg_attempts = StudentAttempt.objects.filter(
                    student__role=role
                ).count() / users.count() if role == 'student' else 0
                
                avg_last_login_days = users.aggregate(
                    avg_days=Avg(
                        F('last_login') - F('date_joined'),
                        output_field=models.DurationField()
                    )
                )['avg_days'] or timedelta(0)
                
                user_engagement.append({
                    'role': role,
                    'total_users': users.count(),
                    'avg_attempts_per_student': avg_attempts,
                    'avg_active_days': avg_last_login_days.days if avg_last_login_days else 0,
                    'active_in_last_30_days': users.filter(
                        last_login__gte=timezone.now() - timedelta(days=30)
                    ).count()
                })
        
        return user_engagement

from django.db.models.functions import TruncMonth
from django.db.models import Count
from django.utils import timezone
from dateutil.relativedelta import relativedelta


class ContentAnalyticsView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    # def get(self, request):
    #     """تحليل المحتوى"""
    #     content_data = {
    #         'total_units': Unit.objects.count(),
    #         'published_units': Unit.objects.filter(is_published=True).count(),
    #         'units_by_difficulty': Unit.objects.values('difficulty').annotate(count=Count('id')),
    #         'most_accessed_units': Unit.objects.annotate(
    #             access_count=Count('student_progress')
    #         ).order_by('-access_count')[:10],
    #         'content_creation_trend': self.get_content_creation_trend(),
    #         'teacher_contribution': self.get_teacher_contribution(),
    #         'content_quality_metrics': self.get_content_quality_metrics()
    #     }
        
    #     return Response(content_data)
    def get(self, request):
        """تحليل المحتوى"""
        content_data = {
            'total_units': Unit.objects.count(),
            'published_units': Unit.objects.filter(is_published=True).count(),
            'units_by_difficulty': list(Unit.objects.values('difficulty').annotate(count=Count('id'))),
            # تحويل QuerySet إلى قائمة من القواميس
            'most_accessed_units': list(Unit.objects.annotate(
                access_count=Count('student_progress')
            ).order_by('-access_count')[:10].values(
                'id', 'title', 'difficulty', 'is_published', 'access_count'
            )),
            'content_creation_trend': self.get_content_creation_trend(),
            'teacher_contribution': self.get_teacher_contribution(),
            'content_quality_metrics': self.get_content_quality_metrics()
        }
        
        return Response(content_data)
    
    # def get_content_creation_trend(self):
    #     """اتجاه إنشاء المحتوى"""
    #     six_months_ago = timezone.now() - relativedelta(months=6)
        
    #     return Unit.objects.filter(
    #         created_at__gte=six_months_ago
    #     ).extra({
    #         'month': "EXTRACT(MONTH FROM created_at)",
    #         'year': "EXTRACT(YEAR FROM created_at)"
    #     }).values('year', 'month').annotate(
    #         count=Count('id')
    #     ).order_by('year', 'month')

    def get_content_creation_trend(self):
        """اتجاه إنشاء المحتوى (متوافق مع SQLite)"""
        six_months_ago = timezone.now() - relativedelta(months=6)
        
        trend_data = Unit.objects.filter(
            created_at__gte=six_months_ago
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # تحويل إلى تنسيق قابل للتسلسل
        return [
            {
                'year': item['month'].year,
                'month': item['month'].month,
                'month_name': item['month'].strftime('%B'),
                'count': item['count']
            }
            for item in trend_data
        ]    
    
    def get_teacher_contribution(self):
        """مساهمة المعلمين في إنشاء المحتوى"""
        teachers = User.objects.filter(role='teacher')
        
        contribution = []
        
        for teacher in teachers:
            units_created = Unit.objects.filter(created_by=teacher).count()
            published_units = Unit.objects.filter(created_by=teacher, is_published=True).count()
            
            if units_created > 0:
                contribution.append({
                    'teacher_id': teacher.id,
                    'teacher_name': teacher.get_full_name(),
                    'units_created': units_created,
                    'published_units': published_units,
                    'publication_rate': (published_units / units_created * 100) if units_created > 0 else 0
                })
        
        # ترتيب حسب عدد الوحدات المنشأة
        contribution.sort(key=lambda x: x['units_created'], reverse=True)
        
        return contribution[:10]  # أفضل 10 معلمين
    
    def get_content_quality_metrics(self):
        """مقاييس جودة المحتوى"""
        units = Unit.objects.all()
        
        quality_metrics = {
            'units_with_video': units.exclude(video_url='').count(),
            'units_with_audio': units.exclude(audio_url='').count(),
            'units_with_thumbnail': units.exclude(thumbnail='').count(),
            'avg_sections_per_unit': units.annotate(
                sections_count=Count('sections')
            ).aggregate(avg=Avg('sections_count'))['avg'] or 0,
            'avg_activities_per_unit': units.annotate(
                activities_count=Count('activities')
            ).aggregate(avg=Avg('activities_count'))['avg'] or 0,
            'units_with_interactive_content': units.filter(
                sections__content_type='interactive'
            ).distinct().count()
        }
        
        return quality_metrics