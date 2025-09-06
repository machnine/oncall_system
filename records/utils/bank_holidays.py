"""
UK Bank Holiday detection utility

This module provides functionality to determine if a given date is a UK bank holiday.
Now uses database storage with automatic sync from UK Government API.
Falls back to hardcoded list if database is not available.
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
    
    try:
        # Try to use database first
        from ..models import BankHoliday
        return BankHoliday.is_bank_holiday(check_date)
    except Exception:
        # Fall back to hardcoded list if database is not available
        return _fallback_is_bank_holiday(check_date)


def get_bank_holidays_for_year(year):
    """
    Get all bank holidays for a specific year.
    
    Args:
        year (int): The year to get bank holidays for
        
    Returns:
        list: List of BankHoliday objects or date objects for bank holidays in that year
        
    Example:
        >>> get_bank_holidays_for_year(2025)
        [<BankHoliday: New Year's Day - 2025-01-01>, ...]
    """
    try:
        # Try to use database first
        from ..models import BankHoliday
        return list(BankHoliday.objects.filter(date__year=year).order_by('date'))
    except Exception:
        # Fall back to hardcoded list
        return [holiday for holiday in _FALLBACK_UK_BANK_HOLIDAYS if holiday.year == year]


def get_next_bank_holiday(from_date=None):
    """
    Get the next bank holiday from a given date (or today if not specified).
    
    Args:
        from_date (date, optional): Date to search from. Defaults to today.
        
    Returns:
        BankHoliday or date or None: The next bank holiday, or None if none found
        
    Example:
        >>> from datetime import date
        >>> get_next_bank_holiday(date(2025, 1, 15))
        <BankHoliday: Good Friday - 2025-04-18>
    """
    if from_date is None:
        from_date = date.today()
    
    try:
        # Try to use database first
        from ..models import BankHoliday
        return BankHoliday.objects.filter(date__gt=from_date).order_by('date').first()
    except Exception:
        # Fall back to hardcoded list
        future_holidays = [holiday for holiday in _FALLBACK_UK_BANK_HOLIDAYS if holiday > from_date]
        return min(future_holidays) if future_holidays else None


def sync_bank_holidays_from_api():
    """
    Sync bank holidays from UK Government API.
    
    Returns:
        dict: Result of the sync operation
    """
    try:
        from ..models import BankHoliday
        return BankHoliday.sync_from_uk_gov_api()
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to sync bank holidays: {str(e)}'
        }


# Fallback hardcoded bank holidays for 2024-2026 (used if database is unavailable)
_FALLBACK_UK_BANK_HOLIDAYS = {
    # 2024
    date(2024, 1, 1),   # New Year's Day
    date(2024, 3, 29),  # Good Friday
    date(2024, 4, 1),   # Easter Monday
    date(2024, 5, 6),   # Early May Bank Holiday
    date(2024, 5, 27),  # Spring Bank Holiday
    date(2024, 8, 26),  # Summer Bank Holiday
    date(2024, 12, 25), # Christmas Day
    date(2024, 12, 26), # Boxing Day
    
    # 2025
    date(2025, 1, 1),   # New Year's Day
    date(2025, 4, 18),  # Good Friday
    date(2025, 4, 21),  # Easter Monday
    date(2025, 5, 5),   # Early May Bank Holiday
    date(2025, 5, 26),  # Spring Bank Holiday
    date(2025, 8, 25),  # Summer Bank Holiday
    date(2025, 12, 25), # Christmas Day
    date(2025, 12, 26), # Boxing Day
    
    # 2026
    date(2026, 1, 1),   # New Year's Day
    date(2026, 4, 3),   # Good Friday
    date(2026, 4, 6),   # Easter Monday
    date(2026, 5, 4),   # Early May Bank Holiday
    date(2026, 5, 25),  # Spring Bank Holiday
    date(2026, 8, 31),  # Summer Bank Holiday
    date(2026, 12, 25), # Christmas Day
    date(2026, 12, 28), # Boxing Day (substitute - 26th is Saturday)
}


def _fallback_is_bank_holiday(check_date):
    """Fallback bank holiday check using hardcoded list"""
    return check_date in _FALLBACK_UK_BANK_HOLIDAYS