"""
health_check/urls.py
"""

from django.urls import path
from core.views import HealthCheckView

urlpatterns = [
    path('', HealthCheckView.as_view(), name='health-check'),
    path('database/', HealthCheckView.as_view(), name='database-health'),
    path('cache/', HealthCheckView.as_view(), name='cache-health'),
]