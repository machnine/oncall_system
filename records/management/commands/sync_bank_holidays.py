"""
Django management command to sync bank holidays from cached file or UK Government API
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from records.models import BankHoliday


class Command(BaseCommand):
    help = 'Sync UK bank holidays from cached file or Government API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            choices=['auto', 'local', 'api'],
            default='auto',
            help='Data source: auto (cached file first, then API), local (cached file only), or api (API only)',
        )
        parser.add_argument(
            '--region',
            choices=['england-and-wales'],
            default='england-and-wales',
            help='Region to sync holidays for (only england-and-wales supported)',
        )
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
        source = options['source']
        region = options['region']
        
        if not options['quiet']:
            source_description = {
                'auto': 'cached file first, then API as fallback',
                'local': 'cached file only',
                'api': 'UK Government API only'
            }
            self.stdout.write(
                self.style.SUCCESS(f'Starting bank holiday sync using {source_description[source]} for {region}...')
            )

        try:
            # Check when we last synced (skip throttling if forcing or using different source)
            if not options['force'] and source == 'api':
                latest_holiday = BankHoliday.objects.order_by('-date').first()
                
                if latest_holiday:
                    days_since_latest = (timezone.now().date() - latest_holiday.date).days
                    
                    # If we have recent holidays and not forcing, suggest using cached file
                    if days_since_latest < 365:  # Don't sync API if we have data from last year
                        if not options['quiet']:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Recent holiday data exists ({latest_holiday.date}). '
                                    f'Consider using --source=local for cached data (2012-2027) or --force to override.'
                                )
                            )
                        return

            # Perform the sync
            result = BankHoliday.sync_bank_holidays(source=source, region=region)

            if result['success']:
                message = (
                    f"Successfully synced {result['total']} bank holidays from {result['source']} ({region}). "
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