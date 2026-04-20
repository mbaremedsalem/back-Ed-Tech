"""
curriculum/views.py - تحديث الـ Views لتعمل مع path
"""

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from .models import Subject, Unit, ContentSection
from .serializers import (
    SubjectSerializer, UnitSerializer, 
    ContentSectionSerializer, UnitDetailSerializer
)
from users.models import User
from assessment.models import StudentProgress

# Subjects Views
# class SubjectListCreateView(generics.ListCreateAPIView):
#     serializer_class = SubjectSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_queryset(self):
#         return Subject.objects.filter(is_active=True)
    
#     def get_permissions(self):
#         if self.request.method == 'POST':
#             return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
#         return [permissions.IsAuthenticated()]
    
#     def get(self, request):
#         subjects = self.get_queryset()
#         serializer = self.get_serializer(subjects, many=True)
#         return Response(serializer.data)
    
#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Subject
from .serializers import SubjectSerializer

class SubjectListCreateView(generics.ListCreateAPIView):
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne les matières selon le rôle de l'utilisateur"""
        user = self.request.user
        base_queryset = Subject.objects.filter(is_active=True)
        
        # Si l'utilisateur est admin -> retourne toutes les matières
        if user.role == 'admin':
            return base_queryset
        
        # Si l'utilisateur est étudiant ou enseignant -> filtre par son grade
        elif user.role in ['student', 'teacher']:
            # Vérifier si l'utilisateur a un grade défini
            if user.grade:
                return base_queryset.filter(grade=user.grade)
            else:
                # Si pas de grade, retourner une liste vide
                return Subject.objects.none()
        
        # Pour tout autre cas
        return Subject.objects.none()
    
    def get_permissions(self):
        """Permissions personnalisées selon la méthode"""
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    def get(self, request):
        """GET avec la même structure de réponse que l'ancienne API"""
        subjects = self.get_queryset()
        serializer = self.get_serializer(subjects, many=True)
        # Retourne exactement le même format que l'ancienne API
        return Response(serializer.data)
    
    def post(self, request):
        """POST avec la même structure de réponse que l'ancienne API"""
        # Vérifier si l'utilisateur est admin
        if request.user.role != 'admin' and not request.user.is_superuser:
            return Response(
                {'detail': 'Seuls les administrateurs peuvent créer des matières'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # Retourne exactement le même format que l'ancienne API
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # Retourne exactement le même format que l'ancienne API
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

class SubjectUnitsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        try:
            subject = Subject.objects.get(pk=pk, is_active=True)
        except Subject.DoesNotExist:
            return Response({'error': 'المادة غير موجودة'}, status=404)
        
        units = subject.units.filter(is_published=True)
        serializer = UnitSerializer(units, many=True, context={'request': request})
        return Response(serializer.data)

# Units Views
class UnitListCreateView(generics.ListCreateAPIView):
    serializer_class = UnitSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'student':
            return Unit.objects.filter(is_published=True)
        elif user.role == 'teacher':
            return Unit.objects.filter(
                Q(is_published=True) | Q(created_by=user)
            )
        elif user.role == 'admin':
            return Unit.objects.all()
        
        return Unit.objects.none()
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    
    def get(self, request):
        units = self.get_queryset()
        serializer = self.get_serializer(units, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UnitDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UnitDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        pk = self.kwargs.get('pk')
        try:
            unit = Unit.objects.get(pk=pk)
            # التحقق من الصلاحيات
            user = self.request.user
            if user.role == 'student' and not unit.is_published:
                raise Unit.DoesNotExist
            return unit
        except Unit.DoesNotExist:
            return None
    
    def get(self, request, pk):
        unit = self.get_object()
        if not unit:
            return Response({'error': 'الوحدة غير موجودة أو غير مصرح بالوصول'}, status=404)
        
        serializer = self.get_serializer(unit, context={'request': request})
        return Response(serializer.data)
    
    def put(self, request, pk):
        unit = self.get_object()
        if not unit:
            return Response({'error': 'الوحدة غير موجودة'}, status=404)
        
        # التحقق من الصلاحيات
        if request.user.role not in ['admin', 'teacher'] or (request.user.role == 'teacher' and unit.created_by != request.user):
            return Response({'error': 'غير مصرح بالتعديل'}, status=403)
        
        serializer = self.get_serializer(unit, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        unit = self.get_object()
        if not unit:
            return Response({'error': 'الوحدة غير موجودة'}, status=404)
        
        # التحقق من الصلاحيات
        if request.user.role not in ['admin', 'teacher'] or (request.user.role == 'teacher' and unit.created_by != request.user):
            return Response({'error': 'غير مصرح بالحذف'}, status=403)
        
        unit.delete()
        return Response({'message': 'تم حذف الوحدة بنجاح'}, status=status.HTTP_204_NO_CONTENT)

class UnitPublishView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            unit = Unit.objects.get(pk=pk)
        except Unit.DoesNotExist:
            return Response({'error': 'الوحدة غير موجودة'}, status=404)
        
        if request.user.role not in ['admin', 'teacher'] or (request.user.role == 'teacher' and unit.created_by != request.user):
            return Response({'error': 'غير مصرح بالنشر'}, status=403)
        
        unit.is_published = True
        unit.save()
        
        return Response({
            'message': 'تم نشر الوحدة بنجاح',
            'unit': UnitSerializer(unit).data
        })

class UnitProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        try:
            unit = Unit.objects.get(pk=pk)
        except Unit.DoesNotExist:
            return Response({'error': 'الوحدة غير موجودة'}, status=404)
        
        if request.user.role == 'student':
            progress, created = StudentProgress.objects.get_or_create(
                student=request.user,
                unit=unit,
                defaults={'mastery_level': 'not_started'}
            )
            from assessment.serializers import StudentProgressSerializer
            serializer = StudentProgressSerializer(progress)
            return Response(serializer.data)
        
        return Response({'error': 'غير مصرح'}, status=403)

# Content Sections Views
class ContentSectionListCreateView(generics.ListCreateAPIView):
    serializer_class = ContentSectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        unit_pk = self.kwargs.get('pk')
        return ContentSection.objects.filter(unit_id=unit_pk).order_by('order')
    
    def get(self, request, pk):
        sections = self.get_queryset()
        serializer = self.get_serializer(sections, many=True)
        return Response(serializer.data)
    
    def post(self, request, pk):
        try:
            unit = Unit.objects.get(pk=pk)
        except Unit.DoesNotExist:
            return Response({'error': 'الوحدة غير موجودة'}, status=404)
        
        # التحقق من الصلاحيات
        if request.user.role not in ['admin', 'teacher'] or (request.user.role == 'teacher' and unit.created_by != request.user):
            return Response({'error': 'غير مصرح بإنشاء محتوى'}, status=403)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(unit=unit)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ContentSectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContentSectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        unit_pk = self.kwargs.get('pk')
        section_id = self.kwargs.get('section_id')
        
        try:
            return ContentSection.objects.get(
                id=section_id,
                unit_id=unit_pk
            )
        except ContentSection.DoesNotExist:
            return None
    
    def get(self, request, pk, section_id):
        section = self.get_object()
        if not section:
            return Response({'error': 'قسم المحتوى غير موجود'}, status=404)
        
        serializer = self.get_serializer(section)
        return Response(serializer.data)
    
    def put(self, request, pk, section_id):
        section = self.get_object()
        if not section:
            return Response({'error': 'قسم المحتوى غير موجود'}, status=404)
        
        # التحقق من الصلاحيات
        if request.user.role not in ['admin', 'teacher'] or (request.user.role == 'teacher' and section.unit.created_by != request.user):
            return Response({'error': 'غير مصرح بالتعديل'}, status=403)
        
        serializer = self.get_serializer(section, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk, section_id):
        section = self.get_object()
        if not section:
            return Response({'error': 'قسم المحتوى غير موجود'}, status=404)
        
        # التحقق من الصلاحيات
        if request.user.role not in ['admin', 'teacher'] or (request.user.role == 'teacher' and section.unit.created_by != request.user):
            return Response({'error': 'غير مصرح بالحذف'}, status=403)
        
        section.delete()
        return Response({'message': 'تم حذف قسم المحتوى بنجاح'}, status=status.HTTP_204_NO_CONTENT)

class AllContentSectionListView(generics.ListAPIView):
    serializer_class = ContentSectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'student':
            return ContentSection.objects.filter(unit__is_published=True)
        elif user.role == 'teacher':
            return ContentSection.objects.filter(
                Q(unit__is_published=True) | Q(unit__created_by=user)
            )
        elif user.role == 'admin':
            return ContentSection.objects.all()
        
        return ContentSection.objects.none()



# # views.py
# import whisper
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework import permissions  # N'oubliez pas d'importer permissions
# import tempfile
# import os

# class WhisperTranscriptionView(APIView):
#     permission_classes = [permissions.AllowAny]
    
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         # Charger le modèle au démarrage
#         self.model = whisper.load_model("base")  # ou "small", "medium", "large"
    
#     def post(self, request, format=None):
#         audio_file = request.FILES.get('audio_file')
        
#         if not audio_file:
#             return Response(
#                 {"error": "Fichier audio requis"}, 
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         # Sauvegarder temporairement le fichier
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
#             for chunk in audio_file.chunks():
#                 tmp_file.write(chunk)
#             tmp_path = tmp_file.name
        
#         try:
#             # SOLUTION 1: Transcription automatique (détection auto de la langue)
#             result = self.model.transcribe(tmp_path)  # Pas de language spécifié
#             transcription = result["text"]
#             detected_language = result["language"]  # Pour vérifier la langue détectée
            
#             return Response(
#                 {
#                     "transcript": transcription,
#                     "detected_language": detected_language  # Optionnel: pour déboguer
#                 }, 
#                 status=status.HTTP_200_OK
#             )
            
#             # SOLUTION 2: Forcer l'arabe explicitement
#             # result = self.model.transcribe(tmp_path, language="ar")
#             # transcription = result["text"]
            
#         except Exception as e:
#             return Response(
#                 {"error": str(e)}, 
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
#         finally:
#             # Nettoyer le fichier temporaire
#             os.unlink(tmp_path)