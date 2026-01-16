"""Risk app configuration."""

from django.apps import AppConfig


class RiskConfig(AppConfig):
    """Risk management app configuration"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'risk'
    verbose_name = 'Risk Management Agent'
