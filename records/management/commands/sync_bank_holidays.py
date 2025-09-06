"""
Django management command to sync bank holidays from UK Government API
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from records.models import BankHoliday


class Command(BaseCommand):
    help = 'Sync UK bank holidays from Government API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sync even if recent data exists',
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Suppress output except for errors',
        )

    def handle(self, *args, **options):
        if not options['quiet']:
            self.stdout.write(
                self.style.SUCCESS('Starting bank holiday sync from UK Government API...')
            )

        try:
            # Check when we last synced
            latest_holiday = BankHoliday.objects.order_by('-updated').first()
            
            if latest_holiday and not options['force']:
                days_since_update = (timezone.now().date() - latest_holiday.updated.date()).days
                
                if days_since_update < 30:  # Don't sync if we've synced in the last 30 days
                    if not options['quiet']:
                        self.stdout.write(
                            f'Last sync was {days_since_update} days ago. Use --force to override.'
                        )
                    return

            # Perform the sync
            result = BankHoliday.sync_from_uk_gov_api()

            if result['success']:
                message = (
                    f"Successfully synced {result['total']} bank holidays. "
                    f"Created: {result['created']}, Updated: {result['updated']}"
                )
                
                if not options['quiet']:
                    self.stdout.write(self.style.SUCCESS(message))
                
                # Log to Django's logging system as well
                import logging
                logger = logging.getLogger('records.bank_holidays')
                logger.info(f"Bank holidays synced: {message}")
                
            else:
                error_message = f"Failed to sync bank holidays: {result['error']}"
                self.stdout.write(self.style.ERROR(error_message))
                
                # Log error
                import logging
                logger = logging.getLogger('records.bank_holidays')
                logger.error(f"Bank holiday sync failed: {result['error']}")

        except Exception as e:
            error_message = f"Unexpected error during bank holiday sync: {str(e)}"
            self.stdout.write(self.style.ERROR(error_message))
            
            # Log error
            import logging
            logger = logging.getLogger('records.bank_holidays')
            logger.exception("Unexpected error during bank holiday sync")