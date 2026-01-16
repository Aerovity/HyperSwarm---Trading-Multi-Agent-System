"""
Root URL configuration for onboarder project.
"""

from django.urls import path, include

urlpatterns = [
    path('api/', include('bridge.urls')),
]
