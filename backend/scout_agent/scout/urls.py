"""
URL configuration for scout project.
"""
from django.urls import path, include

urlpatterns = [
    path('api/', include('markets.urls')),
]
