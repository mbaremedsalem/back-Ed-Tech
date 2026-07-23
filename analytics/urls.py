"""
analytics/urls.py
"""

from django.urls import path

from .views import ClassDashboardView, StudentErrorAnalysisView

urlpatterns = [
    path('class-dashboard/', ClassDashboardView.as_view(), name='class-dashboard'),
    path('students/<int:student_id>/error-analysis/', StudentErrorAnalysisView.as_view(), name='student-error-analysis'),
]
