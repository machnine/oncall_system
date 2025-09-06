"""
UK Bank Holiday detection utility

This module provides functionality to determine if a given date is a UK bank holiday.
Uses the BankHoliday database table with data from UK Government API.
"""

from datetime import date


def is_bank_holiday(check_date):
    """
    Check if a given date is a UK bank holiday.
    
    Args:
        check_date (date): The date to check
        
    Returns:
        bool: True if the date is a bank holiday, False otherwise
        
    Example:
        >>> from datetime import date
        >>> is_bank_holiday(date(2025, 12, 25))
        True
        >>> is_bank_holiday(date(2025, 12, 24))
        False
    """
    if isinstance(check_date, str):
        # Handle string input if needed
        from datetime import datetime
        check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
    
    from ..models import BankHoliday
    return BankHoliday.is_bank_holiday(check_date)


def get_bank_holidays_for_year(year):
    """
    Get all bank holidays for a specific year.
    
    Args:
        year (int): The year to get bank holidays for
        
    Returns:
        list: List of BankHoliday objects for bank holidays in that year
        
    Example:
        >>> get_bank_holidays_for_year(2025)
        [<BankHoliday: New Year's Day - 2025-01-01>, ...]
    """
    from ..models import BankHoliday
    return list(BankHoliday.objects.filter(date__year=year).order_by('date'))


def get_next_bank_holiday(from_date=None):
    """
    Get the next bank holiday from a given date (or today if not specified).
    
    Args:
        from_date (date, optional): Date to search from. Defaults to today.
        
    Returns:
        BankHoliday or None: The next bank holiday, or None if none found
        
    Example:
        >>> from datetime import date
        >>> get_next_bank_holiday(date(2025, 1, 15))
        <BankHoliday: Good Friday - 2025-04-18>
    """
    if from_date is None:
        from_date = date.today()
    
    from ..models import BankHoliday
    return BankHoliday.objects.filter(date__gt=from_date).order_by('date').first()


def sync_bank_holidays_from_api():
    """
    Sync bank holidays from UK Government API.
    
    Returns:
        dict: Result of the sync operation
    """
    from ..models import BankHoliday
    return BankHoliday.sync_from_uk_gov_api()