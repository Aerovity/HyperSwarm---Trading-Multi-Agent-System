"""
URL configuration for executor project.
"""

from django.urls import path, include

urlpatterns = [
    path('api/', include('trading.urls')),
]
