"""
skills/views.py
"""

from django.db.models import Count
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from curriculum.views import IsTeacherOrAdminOrReadOnly
from .models import Skill, Prerequisite, Chunk
from .serializers import (
    SkillListSerializer,
    SkillDetailSerializer,
    PrerequisiteSerializer,
    ChunkSerializer,
)


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.select_related('goal').prefetch_related('chunks', 'prerequisites_required').all()
    permission_classes = [IsTeacherOrAdminOrReadOnly]
    filterset_fields = ['goal', 'skill_type', 'difficulty']
    search_fields = ['code', 'name']

    def get_serializer_class(self):
        if self.action == 'list':
            return SkillListSerializer
        return SkillDetailSerializer

    @action(detail=True, methods=['get'])
    def prerequisites(self, request, pk=None):
        skill = self.get_object()
        data = PrerequisiteSerializer(skill.prerequisites_required.all(), many=True).data
        return Response(data)

    @action(detail=True, methods=['get'])
    def publication_check(self, request, pk=None):
        """
        Vérifie la règle CMS (min. 1 rule, 1 example, 2 practice)
        avant de permettre la publication du contenu de la skill.
        """
        skill = self.get_object()
        ready = skill.chunks_meet_minimum()
        counts = {
            c['chunk_type']: c['n']
            for c in skill.chunks.values('chunk_type').annotate(n=Count('id'))
        }
        return Response({'ready': ready, 'chunk_counts': counts})


class PrerequisiteViewSet(viewsets.ModelViewSet):
    queryset = Prerequisite.objects.select_related('skill', 'prerequisite').all()
    serializer_class = PrerequisiteSerializer
    permission_classes = [IsTeacherOrAdminOrReadOnly]
    filterset_fields = ['skill', 'prerequisite']


class ChunkViewSet(viewsets.ModelViewSet):
    queryset = Chunk.objects.select_related('skill').all()
    serializer_class = ChunkSerializer
    permission_classes = [IsTeacherOrAdminOrReadOnly]
    filterset_fields = ['skill', 'chunk_type', 'difficulty']
    search_fields = ['code', 'title', 'content']
