"""
curriculum/serializers.py
"""

from rest_framework import serializers
from .models import Subject, Unit, ContentSection
from assessment.models import StudentProgress
from assessment.serializers import ActivitySerializer

class SubjectSerializer(serializers.ModelSerializer):
    unit_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'grade', 'description', 'icon', 
            'color', 'is_active', 'created_at', 'updated_at', 'unit_count'
        ]
    
    def get_unit_count(self, obj):
        return obj.units.count()

class ContentSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentSection
        fields = '__all__'

class UnitSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    activity_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Unit
        fields = [
            'id', 'subject', 'subject_name', 'title', 'description', 
            'learning_objective', 'duration_minutes', 'difficulty', 'order',
            'thumbnail', 'video_url', 'audio_url', 'is_published', 
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'activity_count'
        ]
        read_only_fields = ('created_by',)
    
    def get_activity_count(self, obj):
        return obj.activities.count()

class UnitDetailSerializer(UnitSerializer):
    sections = ContentSectionSerializer(many=True, read_only=True)
    activities = ActivitySerializer(many=True, read_only=True)
    student_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Unit
        fields = [
            'id', 'subject', 'subject_name', 'title', 'description', 
            'learning_objective', 'duration_minutes', 'difficulty', 'order',
            'thumbnail', 'video_url', 'audio_url', 'is_published', 
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'activity_count', 'sections', 'activities', 'student_progress'
        ]
        read_only_fields = ('created_by',)
    
    def get_student_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.role == 'student':
            try:
                progress = StudentProgress.objects.get(
                    student=request.user,
                    unit=obj
                )
                from assessment.serializers import StudentProgressSerializer
                return StudentProgressSerializer(progress).data
            except StudentProgress.DoesNotExist:
                return None
        return None