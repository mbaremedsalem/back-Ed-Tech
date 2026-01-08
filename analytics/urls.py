"""
analytics/urls.py
"""

from django.urls import path
from . import views

urlpatterns = [
    # Learning Analytics endpoints
    path('learning/', views.LearningAnalyticsListView.as_view(), name='learning-analytics-list'),
    path('learning/daily-report/', views.DailyLearningReportView.as_view(), name='daily-learning-report'),
    path('learning/student/<int:student_id>/', views.StudentLearningAnalyticsView.as_view(), name='student-learning-analytics'),
    
    # Teacher Dashboard endpoints
    path('teacher-dashboard/', views.TeacherDashboardView.as_view(), name='teacher-dashboard'),
    path('teacher-dashboard/overview/', views.TeacherDashboardOverviewView.as_view(), name='teacher-dashboard-overview'),
    path('teacher-dashboard/students-progress/', views.TeacherStudentsProgressView.as_view(), name='teacher-students-progress'),
    path('teacher-dashboard/units-performance/', views.TeacherUnitsPerformanceView.as_view(), name='teacher-units-performance'),
    
    # System Logs endpoints
    path('system-logs/', views.SystemLogListView.as_view(), name='system-logs-list'),
    path('system-logs/security-report/', views.SecurityReportView.as_view(), name='security-report'),
    path('system-logs/error-logs/', views.ErrorLogsView.as_view(), name='error-logs'),
    
    # Reports endpoints
    path('reports/', views.AnalyticsReportAPIView.as_view(), name='analytics-reports'),
    path('reports/usage/', views.UsageAnalyticsView.as_view(), name='usage-analytics'),
    path('reports/performance/', views.PerformanceAnalyticsView.as_view(), name='performance-analytics'),
    path('reports/users/', views.UserAnalyticsView.as_view(), name='user-analytics'),
    path('reports/content/', views.ContentAnalyticsView.as_view(), name='content-analytics'),
]