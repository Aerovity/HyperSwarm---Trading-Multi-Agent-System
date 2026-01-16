"""URL configuration for risk app."""

from django.urls import path
from . import views

urlpatterns = [
    # Health and monitoring
    path('health', views.health_check, name='health_check'),
    path('agent/logs', views.agent_logs, name='agent_logs'),

    # Portfolio and positions
    path('portfolio/state', views.portfolio_state, name='portfolio_state'),
    path('positions', views.get_positions, name='positions'),

    # Risk analysis
    path('risk/metrics', views.risk_metrics, name='risk_metrics'),
    path('alerts', views.get_alerts, name='alerts'),

    # Trade approval (LLM-powered)
    path('trade/approve', views.approve_trade, name='approve_trade'),
]
