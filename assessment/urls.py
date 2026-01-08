"""
assessment/urls.py
"""

from django.urls import path
from . import views

urlpatterns = [
    # Activities endpoints
    path('units/<int:unit_id>/activities/', views.UnitActivityListCreateView.as_view(), name='unit-activities'),
    path('activities/', views.ActivityListView.as_view(), name='activity-list'),
    path('activities/<int:pk>/', views.ActivityDetailView.as_view(), name='activity-detail'),
    
    # Student Attempts endpoints
    path('activities/<int:activity_id>/attempts/', views.ActivityAttemptListCreateView.as_view(), name='activity-attempts'),
    path('attempts/', views.AttemptListView.as_view(), name='attempt-list'),
    path('attempts/<int:pk>/', views.AttemptDetailView.as_view(), name='attempt-detail'),
    
    # Student Progress endpoints
    path('progress/', views.StudentProgressListView.as_view(), name='progress-list'),
    path('progress/summary/', views.StudentProgressSummaryView.as_view(), name='progress-summary'),
    path('progress/units/<int:unit_id>/', views.UnitProgressDetailView.as_view(), name='unit-progress-detail'),
    
    # Submission endpoints
    path('submit/activity/<int:activity_id>/', views.SubmitActivityView.as_view(), name='submit-activity'),
]