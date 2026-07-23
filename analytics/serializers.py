"""
analytics/serializers.py

Serializers "de sortie" uniquement : ils mettent en forme des résultats
de requêtes agrégées, ils ne sont adossés à aucun modèle dédié
(voir analytics/models.py).
"""

from rest_framework import serializers


class ClassDashboardRowSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    skills_started = serializers.IntegerField()
    skills_mastered = serializers.IntegerField()
    average_mastery = serializers.FloatField()
    last_active = serializers.DateTimeField(allow_null=True)


class StudentErrorAnalysisRowSerializer(serializers.Serializer):
    skill_name = serializers.CharField()
    error_category = serializers.CharField()
    error_code = serializers.CharField(allow_null=True)
    root_cause = serializers.CharField(allow_null=True)
    severity_level = serializers.CharField(allow_null=True)
    occurrences = serializers.IntegerField()
