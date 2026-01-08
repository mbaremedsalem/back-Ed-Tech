"""
assessment/serializers.py
"""

from rest_framework import serializers
from .models import Activity, StudentAttempt, StudentProgress

class ActivitySerializer(serializers.ModelSerializer):
    unit_title = serializers.CharField(source='unit.title', read_only=True)
    
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ('unit',)

class ActivitySubmissionSerializer(serializers.Serializer):
    answer = serializers.JSONField()
    time_taken = serializers.IntegerField(min_value=0)

class StudentAttemptSerializer(serializers.ModelSerializer):
    activity_title = serializers.CharField(source='activity.title', read_only=True)
    activity_type = serializers.CharField(source='activity.activity_type', read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    
    class Meta:
        model = StudentAttempt
        fields = '__all__'
        read_only_fields = ('student', 'activity', 'is_correct', 'score')

class StudentProgressSerializer(serializers.ModelSerializer):
    unit_title = serializers.CharField(source='unit.title', read_only=True)
    subject_name = serializers.CharField(source='unit.subject.name', read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    completed_activities_count = serializers.SerializerMethodField()
    total_activities_count = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentProgress
        fields = '__all__'
    
    def get_completed_activities_count(self, obj):
        return obj.completed_activities.count()
    
    def get_total_activities_count(self, obj):
        return obj.unit.activities.filter(is_active=True).count()