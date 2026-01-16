"""
URL patterns for trading API endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('health', views.health_check, name='health_check'),
    path('agent/logs', views.agent_logs, name='agent_logs'),
    path('positions', views.list_positions, name='list_positions'),
    path('positions/<str:position_id>', views.get_position, name='get_position'),
    path('positions/<str:position_id>/close', views.close_position, name='close_position'),
    path('trades/execute', views.execute_trade, name='execute_trade'),
    path('emergency_stop', views.emergency_stop, name='emergency_stop'),
]
