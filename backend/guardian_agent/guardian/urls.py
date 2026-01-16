"""
URL configuration for Guardian Agent project.
"""

from django.urls import path, include

urlpatterns = [
    path('api/', include('risk.urls')),
]
