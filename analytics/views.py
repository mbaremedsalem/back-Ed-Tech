"""
analytics/views.py

Implémente les deux requêtes du scénario "Ahmed / Sarah" (Partie 6,
Étapes 12 et 13) : tableau de bord de classe et analyse détaillée des
erreurs d'un étudiant. Aucune table dédiée : tout est calculé à la volée
(voir Partie 7.3, "Points de vigilance").
"""

from datetime import timedelta

from django.db.models import Avg, Count, Max, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from assessment.models import LogAnswer, StudentProgress
from users.models import User
from .serializers import ClassDashboardRowSerializer, StudentErrorAnalysisRowSerializer


class IsTeacherOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.TEACHER, User.Role.REGIONAL_ADMIN, User.Role.ADMIN)
        )


class ClassDashboardView(APIView):
    """
    GET /api/analytics/class-dashboard/?level=<id>

    Équivalent de la requête agrégée de l'Étape 12 : pour chaque
    étudiant, nombre de skills commencées, nombre de skills maîtrisées,
    mastery moyen, dernière activité.
    """
    permission_classes = [IsTeacherOrAdmin]

    def get(self, request):
        students = User.objects.filter(role=User.Role.STUDENT)

        level_id = request.query_params.get('level')
        if level_id:
            students = students.filter(student_profile__level_id=level_id)

        students = students.annotate(
            skills_started=Count('progress__skill', distinct=True),
            skills_mastered=Count(
                'progress__skill',
                filter=Q(progress__status=StudentProgress.Status.MASTERED),
                distinct=True,
            ),
            average_mastery=Avg('progress__mastery'),
            last_active=Max('progress__last_activity'),
        ).order_by('-average_mastery')

        rows = [
            {
                'student_id': s.id,
                'username': s.username,
                'first_name': s.first_name,
                'last_name': s.last_name,
                'skills_started': s.skills_started,
                'skills_mastered': s.skills_mastered,
                'average_mastery': float(s.average_mastery) if s.average_mastery is not None else 0.0,
                'last_active': s.last_active,
            }
            for s in students
        ]
        serializer = ClassDashboardRowSerializer(rows, many=True)
        return Response(serializer.data)


class StudentErrorAnalysisView(APIView):
    """
    GET /api/analytics/students/<student_id>/error-analysis/?days=7

    Équivalent de la requête de l'Étape 13 : erreurs récentes d'un
    étudiant, groupées par skill / catégorie / détail d'erreur.
    """
    permission_classes = [IsTeacherOrAdmin]

    def get(self, request, student_id):
        student = get_object_or_404(User, pk=student_id, role=User.Role.STUDENT)

        days = int(request.query_params.get('days', 7))
        since = timezone.now() - timedelta(days=days)

        qs = (
            LogAnswer.objects
            .filter(student=student, is_correct=False, timestamp__gte=since)
            .values(
                'skill__name',
                'error_type',
                'error_detail__code',
                'error_detail__root_cause',
                'error_detail__severity_level',
            )
            .annotate(occurrences=Count('id'))
            .order_by('-occurrences')
        )

        rows = [
            {
                'skill_name': r['skill__name'],
                'error_category': r['error_type'],
                'error_code': r['error_detail__code'],
                'root_cause': r['error_detail__root_cause'],
                'severity_level': r['error_detail__severity_level'],
                'occurrences': r['occurrences'],
            }
            for r in qs
        ]
        serializer = StudentErrorAnalysisRowSerializer(rows, many=True)
        return Response(serializer.data)
