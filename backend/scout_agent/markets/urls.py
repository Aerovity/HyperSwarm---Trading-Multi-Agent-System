"""
URL configuration for markets app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('markets/live', views.live_markets, name='live_markets'),
    path('signals/recent', views.recent_signals, name='recent_signals'),
    path('signals/analyze', views.analyze_and_signal, name='analyze_and_signal'),
    path('pairs/correlations', views.pair_correlations, name='pair_correlations'),
    path('spread/history', views.spread_history, name='spread_history'),
    path('agent/logs', views.agent_logs, name='agent_logs'),
    path('health', views.health_check, name='health_check'),
]
