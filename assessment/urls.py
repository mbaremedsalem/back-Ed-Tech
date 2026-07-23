# assessment/urls.py

from django.urls import path
from .views import ErrorViewSet, StudentProgressViewSet, LogAnswerViewSet

urlpatterns = [
    # Errors
    path('errors/', ErrorViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='error-list'),
    path('errors/<int:pk>/', ErrorViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='error-detail'),
    
    # Student Progress
    path('progress/', StudentProgressViewSet.as_view({
        'get': 'list'
        # 'post': 'create'
    }), name='student-progress-list'),
    path('progress/<int:pk>/', StudentProgressViewSet.as_view({
        'get': 'retrieve',
        # 'put': 'update',
        # 'patch': 'partial_update',
        # 'delete': 'destroy'
    }), name='student-progress-detail'),
    
    # Log Answers
    path('log-answers/', LogAnswerViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='log-answer-list'),
    path('log-answers/<int:pk>/', LogAnswerViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='log-answer-detail'),
]