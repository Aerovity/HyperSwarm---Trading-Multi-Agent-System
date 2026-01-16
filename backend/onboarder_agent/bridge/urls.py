"""
URL configuration for bridge app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Bridge operations
    path('bridge/quote', views.get_bridge_quote, name='bridge_quote'),
    path('bridge/execute', views.execute_bridge, name='bridge_execute'),
    path('bridge/status/<str:tx_id>', views.get_bridge_status, name='bridge_status'),
    path('bridge/chains', views.get_supported_chains, name='supported_chains'),
    path('bridge/balance/<str:address>', views.get_user_balance, name='user_balance'),

    # Agent monitoring
    path('agent/logs', views.agent_logs, name='agent_logs'),
    path('health', views.health_check, name='health_check'),
]
