"""
analytics/serializers.py
"""

from rest_framework import serializers
from .models import LearningAnalytics, TeacherDashboard, SystemLog

class LearningAnalyticsSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    
    class Meta:
        model = LearningAnalytics
        fields = [
            'id', 'student', 'student_name', 'date', 'total_time_spent',
            'completed_units', 'total_score', 'avg_mastery_level'
        ]

class TeacherDashboardSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    
    class Meta:
        model = TeacherDashboard
        fields = [
            'id', 'teacher', 'teacher_name', 'total_students', 
            'active_students', 'total_units_created', 
            'student_engagement_rate', 'avg_student_progress', 
            'last_updated'
        ]

class SystemLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = SystemLog
        fields = [
            'id', 'level', 'category', 'message', 'user', 'user_name',
            'ip_address', 'user_agent', 'created_at'
        ]

class AnalyticsReportSerializer(serializers.Serializer):
    usage_analytics = serializers.DictField()
    performance_analytics = serializers.DictField()
    user_analytics = serializers.DictField()
    content_analytics = serializers.DictField()
    generated_at = serializers.DateTimeField()