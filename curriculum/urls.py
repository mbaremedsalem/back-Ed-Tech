"""
curriculum/urls.py
"""

from django.urls import path
from . import views

urlpatterns = [
    # Subjects endpoints
    path('subjects/', views.SubjectListCreateView.as_view(), name='subject-list'),
    path('subjects/<int:pk>/', views.SubjectDetailView.as_view(), name='subject-detail'),
    path('subjects/<int:pk>/units/', views.SubjectUnitsView.as_view(), name='subject-units'),
    
    # Units endpoints
    path('units/', views.UnitListCreateView.as_view(), name='unit-list'),
    path('units/<int:pk>/', views.UnitDetailView.as_view(), name='unit-detail'),
    path('units/<int:pk>/publish/', views.UnitPublishView.as_view(), name='unit-publish'),
    path('units/<int:pk>/progress/', views.UnitProgressView.as_view(), name='unit-progress'),
    path('units/<int:pk>/sections/', views.ContentSectionListCreateView.as_view(), name='section-list'),
    path('units/<int:pk>/sections/<int:section_id>/', views.ContentSectionDetailView.as_view(), name='section-detail'),
    
    # Content Sections endpoints
    path('sections/', views.AllContentSectionListView.as_view(), name='all-sections'),
]