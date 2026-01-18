"""
URL configuration for chat app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('orchestrator/chat', views.chat, name='chat'),
    path('agent/logs', views.agent_logs, name='agent_logs'),
    path('health', views.health_check, name='health'),
]
