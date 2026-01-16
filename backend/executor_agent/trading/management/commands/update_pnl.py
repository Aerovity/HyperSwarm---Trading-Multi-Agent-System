"""
Django management command to run the PnL updater daemon.
Updates position PnL every 5 seconds using Scout's real-time market data.
"""

import time
import logging
from django.core.management.base import BaseCommand
from trading.pnl_updater import PnLUpdater

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run PnL updater daemon to sync positions with Scout market data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Update interval in seconds (default: 5)'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        updater = PnLUpdater()

        self.stdout.write(
            self.style.SUCCESS(
                f'PnL Updater started - updating positions every {interval}s'
            )
        )

        try:
            while True:
                try:
                    updater.update_all_positions()
                except Exception as e:
                    logger.error(f"Error in PnL update cycle: {e}")
                    self.stdout.write(
                        self.style.ERROR(f"Update failed: {e}")
                    )

                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nPnL Updater stopped by user')
            )
