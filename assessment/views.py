"""
assessment/views.py - تحديث الـ Views لتعمل مع path
"""

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta

from curriculum.serializers import UnitSerializer
from .models import Activity, StudentAttempt, StudentProgress
from .serializers import (
    ActivitySerializer, StudentAttemptSerializer,
    StudentProgressSerializer, ActivitySubmissionSerializer
)
from curriculum.models import Unit

# Activities Views
class UnitActivityListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, unit_id):
        try:
            unit = Unit.objects.get(pk=unit_id)
        except Unit.DoesNotExist:
            return Response({'error': 'الوحدة غير موجودة'}, status=404)
        
        user = request.user
        activities = unit.activities.all()
        
        if user.role == 'student':
            activities = activities.filter(is_active=True)
        
        serializer = ActivitySerializer(activities, many=True)
        return Response(serializer.data)
    
    def post(self, request, unit_id):
        try:
            unit = Unit.objects.get(pk=unit_id)
        except Unit.DoesNotExist:
            return Response({'error': 'الوحدة غير موجودة'}, status=404)
        
        if request.user.role not in ['admin', 'teacher'] or (request.user.role == 'teacher' and unit.created_by != request.user):
            return Response({'error': 'غير مصرح بإنشاء نشاط'}, status=403)
        
        serializer = ActivitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(unit=unit)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ActivityListView(generics.ListAPIView):
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'student':
            return Activity.objects.filter(is_active=True)
        elif user.role == 'teacher':
            return Activity.objects.filter(unit__created_by=user)
        elif user.role == 'admin':
            return Activity.objects.all()
        
        return Activity.objects.none()
    
    def get(self, request):
        activities = self.get_queryset()
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)

class ActivityDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        pk = self.kwargs.get('pk')
        try:
            activity = Activity.objects.get(pk=pk)
            return activity
        except Activity.DoesNotExist:
            return None
    
    def get(self, request, pk):
        activity = self.get_object()
        if not activity:
            return Response({'error': 'النشاط غير موجود'}, status=404)
        
        # التحقق من الصلاحيات للطلاب
        if request.user.role == 'student' and not activity.is_active:
            return Response({'error': 'النشاط غير متاح'}, status=403)
        
        serializer = self.get_serializer(activity)
        return Response(serializer.data)
    
    def put(self, request, pk):
        activity = self.get_object()
        if not activity:
            return Response({'error': 'النشاط غير موجود'}, status=404)
        
        # التحقق من الصلاحيات
        if request.user.role not in ['admin', 'teacher'] or (request.user.role == 'teacher' and activity.unit.created_by != request.user):
            return Response({'error': 'غير مصرح بالتعديل'}, status=403)
        
        serializer = self.get_serializer(activity, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        activity = self.get_object()
        if not activity:
            return Response({'error': 'النشاط غير موجود'}, status=404)
        
        # التحقق من الصلاحيات
        if request.user.role not in ['admin', 'teacher'] or (request.user.role == 'teacher' and activity.unit.created_by != request.user):
            return Response({'error': 'غير مصرح بالحذف'}, status=403)
        
        activity.delete()
        return Response({'message': 'تم حذف النشاط بنجاح'}, status=status.HTTP_204_NO_CONTENT)

# Student Attempts Views
class ActivityAttemptListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, activity_id):
        try:
            activity = Activity.objects.get(pk=activity_id)
        except Activity.DoesNotExist:
            return Response({'error': 'النشاط غير موجود'}, status=404)
        
        user = request.user
        
        if user.role == 'student':
            attempts = StudentAttempt.objects.filter(
                student=user,
                activity=activity
            )
        elif user.role == 'teacher':
            attempts = StudentAttempt.objects.filter(activity=activity)
        elif user.role == 'admin':
            attempts = StudentAttempt.objects.all()
        else:
            attempts = StudentAttempt.objects.none()
        
        serializer = StudentAttemptSerializer(attempts, many=True)
        return Response(serializer.data)
    
    def post(self, request, activity_id):
        try:
            activity = Activity.objects.get(pk=activity_id)
        except Activity.DoesNotExist:
            return Response({'error': 'النشاط غير موجود'}, status=404)
        
        if request.user.role != 'student':
            return Response({'error': 'الطلاب فقط يمكنهم تقديم محاولات'}, status=403)
        
        serializer = ActivitySubmissionSerializer(data=request.data)
        if serializer.is_valid():
            answer = serializer.validated_data['answer']
            time_taken = serializer.validated_data['time_taken']
            
            # التحقق من صحة الإجابة
            is_correct = self.check_answer(activity, answer)
            score = activity.points if is_correct else 0
            
            # إنشاء المحاولة
            attempt = StudentAttempt.objects.create(
                student=request.user,
                activity=activity,
                answer=answer,
                is_correct=is_correct,
                score=score,
                time_taken=time_taken
            )
            
            # تحديث تقدم الطالب
            self.update_student_progress(attempt)
            
            result_serializer = StudentAttemptSerializer(attempt)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def check_answer(self, activity, student_answer):
        """التحقق من صحة الإجابة"""
        correct_answer = activity.correct_answer
        
        if activity.activity_type == 'multiple_choice':
            return student_answer == correct_answer
        elif activity.activity_type == 'true_false':
            return student_answer == correct_answer
        elif activity.activity_type == 'fill_blank':
            return str(student_answer).lower().strip() == str(correct_answer).lower().strip()
        
        return False
    
    def update_student_progress(self, attempt):
        """تحديث تقدم الطالب"""
        student = attempt.student
        activity = attempt.activity
        unit = activity.unit
        
        # الحصول على التقدم أو إنشاء جديد
        progress, created = StudentProgress.objects.get_or_create(
            student=student,
            unit=unit,
            defaults={
                'mastery_level': 'beginner',
                'total_score': 0
            }
        )
        
        # تحديث إذا كانت الإجابة صحيحة
        if attempt.is_correct and activity not in progress.completed_activities.all():
            progress.completed_activities.add(activity)
            progress.total_score += attempt.score
        
        progress.last_accessed = timezone.now()
        
        # إذا أكمل جميع الأنشطة
        total_activities = unit.activities.filter(is_active=True).count()
        completed_count = progress.completed_activities.count()
        
        if completed_count == total_activities:
            progress.completed_at = timezone.now()
        
        # تحديث النسبة المئوية
        progress.update_progress()

class AttemptListView(generics.ListAPIView):
    serializer_class = StudentAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'student':
            return StudentAttempt.objects.filter(student=user)
        elif user.role == 'teacher':
            return StudentAttempt.objects.filter(
                activity__unit__created_by=user
            )
        elif user.role == 'admin':
            return StudentAttempt.objects.all()
        
        return StudentAttempt.objects.none()
    
    def get(self, request):
        attempts = self.get_queryset()
        serializer = self.get_serializer(attempts, many=True)
        return Response(serializer.data)

class AttemptDetailView(generics.RetrieveAPIView):
    serializer_class = StudentAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        pk = self.kwargs.get('pk')
        try:
            attempt = StudentAttempt.objects.get(pk=pk)
            
            # التحقق من الصلاحيات
            user = self.request.user
            if user.role == 'student' and attempt.student != user:
                return None
            elif user.role == 'teacher' and attempt.activity.unit.created_by != user:
                return None
            
            return attempt
        except StudentAttempt.DoesNotExist:
            return None
    
    def get(self, request, pk):
        attempt = self.get_object()
        if not attempt:
            return Response({'error': 'المحاولة غير موجودة أو غير مصرح بالوصول'}, status=404)
        
        serializer = self.get_serializer(attempt)
        return Response(serializer.data)

# Student Progress Views
class StudentProgressListView(generics.ListAPIView):
    serializer_class = StudentProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'student':
            return StudentProgress.objects.filter(student=user)
        elif user.role == 'teacher':
            teacher_units = Unit.objects.filter(created_by=user)
            return StudentProgress.objects.filter(unit__in=teacher_units)
        elif user.role == 'admin':
            return StudentProgress.objects.all()
        
        return StudentProgress.objects.none()
    
    def get(self, request):
        progress = self.get_queryset()
        serializer = self.get_serializer(progress, many=True)
        return Response(serializer.data)

class StudentProgressSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if user.role != 'student':
            return Response({'error': 'غير مصرح'}, status=403)
        
        progress_data = StudentProgress.objects.filter(student=user)
        
        summary = {
            'total_units': progress_data.count(),
            'completed_units': progress_data.filter(completion_percentage=100).count(),
            'in_progress_units': progress_data.filter(
                completion_percentage__gt=0,
                completion_percentage__lt=100
            ).count(),
            'average_progress': progress_data.aggregate(Avg('completion_percentage'))['completion_percentage__avg'] or 0,
            'total_score': progress_data.aggregate(Sum('total_score'))['total_score__sum'] or 0,
            'mastery_distribution': progress_data.values('mastery_level').annotate(
                count=Count('id')
            ).order_by('mastery_level')
        }
        
        # إحصائيات الأسبوع الأخير
        last_week = timezone.now() - timedelta(days=7)
        weekly_progress = StudentProgress.objects.filter(
            student=user,
            last_accessed__gte=last_week
        )
        summary['weekly_completed'] = weekly_progress.filter(completion_percentage=100).count()
        summary['weekly_score'] = weekly_progress.aggregate(Sum('total_score'))['total_score__sum'] or 0
        
        return Response(summary)

class UnitProgressDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, unit_id):
        try:
            unit = Unit.objects.get(pk=unit_id)
        except Unit.DoesNotExist:
            return Response({'error': 'الوحدة غير موجودة'}, status=404)
        
        user = request.user
        
        if user.role == 'student':
            try:
                progress = StudentProgress.objects.get(
                    student=user,
                    unit=unit
                )
                serializer = StudentProgressSerializer(progress)
                return Response(serializer.data)
            except StudentProgress.DoesNotExist:
                return Response({
                    'unit': unit.title,
                    'message': 'لم تبدأ هذه الوحدة بعد',
                    'progress': 0,
                    'mastery_level': 'not_started'
                })
        
        elif user.role in ['teacher', 'admin']:
            # للمعلمين والمديرين: عرض تقدم جميع الطلاب في هذه الوحدة
            progress_data = StudentProgress.objects.filter(unit=unit)
            serializer = StudentProgressSerializer(progress_data, many=True)
            
            stats = {
                'total_students': progress_data.count(),
                'average_progress': progress_data.aggregate(Avg('completion_percentage'))['completion_percentage__avg'] or 0,
                'completed_count': progress_data.filter(completion_percentage=100).count(),
                'mastery_distribution': progress_data.values('mastery_level').annotate(count=Count('id'))
            }
            
            return Response({
                'unit': UnitSerializer(unit).data,
                'students_progress': serializer.data,
                'statistics': stats
            })
        
        return Response({'error': 'غير مصرح'}, status=403)

# Submission View
class SubmitActivityView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, activity_id):
        try:
            activity = Activity.objects.get(pk=activity_id, is_active=True)
        except Activity.DoesNotExist:
            return Response({'error': 'النشاط غير موجود أو غير مفعل'}, status=404)
        
        if request.user.role != 'student':
            return Response({'error': 'الطلاب فقط يمكنهم تقديم الأنشطة'}, status=403)
        
        serializer = ActivitySubmissionSerializer(data=request.data)
        if serializer.is_valid():
            # نفس المنطق الموجود في ActivityAttemptListCreateView
            answer = serializer.validated_data['answer']
            time_taken = serializer.validated_data['time_taken']
            
            # التحقق من صحة الإجابة
            is_correct = self.check_answer(activity, answer)
            score = activity.points if is_correct else 0
            
            # إنشاء المحاولة
            attempt = StudentAttempt.objects.create(
                student=request.user,
                activity=activity,
                answer=answer,
                is_correct=is_correct,
                score=score,
                time_taken=time_taken
            )
            
            # تحديث التقدم
            self.update_student_progress(attempt)
            
            # إرجاع النتيجة
            return Response({
                'success': True,
                'is_correct': is_correct,
                'score': score,
                'correct_answer': activity.correct_answer if not is_correct else None,
                'explanation': activity.explanation if is_correct else 'جرّب مرة أخرى',
                'attempt_id': attempt.id
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def check_answer(self, activity, student_answer):
        """التحقق من صحة الإجابة"""
        correct_answer = activity.correct_answer
        
        if activity.activity_type == 'multiple_choice':
            return student_answer == correct_answer
        elif activity.activity_type == 'true_false':
            return student_answer == correct_answer
        elif activity.activity_type == 'fill_blank':
            return str(student_answer).lower().strip() == str(correct_answer).lower().strip()
        
        return False
    
    def update_student_progress(self, attempt):
        """تحديث تقدم الطالب"""
        student = attempt.student
        activity = attempt.activity
        unit = activity.unit
        
        # الحصول على التقدم أو إنشاء جديد
        progress, created = StudentProgress.objects.get_or_create(
            student=student,
            unit=unit,
            defaults={
                'mastery_level': 'beginner',
                'total_score': 0
            }
        )
        
        # تحديث إذا كانت الإجابة صحيحة
        if attempt.is_correct and activity not in progress.completed_activities.all():
            progress.completed_activities.add(activity)
            progress.total_score += attempt.score
        
        progress.last_accessed = timezone.now()
        progress.update_progress()