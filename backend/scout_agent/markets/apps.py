"""
Django app configuration for markets app.
"""

from django.apps import AppConfig


class MarketsConfig(AppConfig):
    """Configuration for markets Django app"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'markets'
    verbose_name = 'Markets'

    def ready(self):
        """
        App initialization code.
        This runs when Django starts.
        """
        # Import and start WebSocket client
        from .websocket_client import HyperliquidWebSocketClient
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Start WebSocket client in background
            ws_client = HyperliquidWebSocketClient()
            ws_client.start()
            logger.info("WebSocket client started on app ready")
        except Exception as e:
            logger.error(f"Failed to start WebSocket client: {e}")
