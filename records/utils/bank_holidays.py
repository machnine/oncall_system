"""
UK Bank Holiday detection utility

This module provides functionality to determine if a given date is a UK bank holiday.
Currently uses a simple hardcoded list but could be extended to use an API or more
sophisticated calculation in the future.
"""

from datetime import date


# UK Bank Holidays for 2024-2026 (extend as needed)
UK_BANK_HOLIDAYS = {
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
    
    return check_date in UK_BANK_HOLIDAYS


def get_bank_holidays_for_year(year):
    """
    Get all bank holidays for a specific year.
    
    Args:
        year (int): The year to get bank holidays for
        
    Returns:
        list: List of date objects for bank holidays in that year
        
    Example:
        >>> get_bank_holidays_for_year(2025)
        [date(2025, 1, 1), date(2025, 4, 18), ...]
    """
    return [holiday for holiday in UK_BANK_HOLIDAYS if holiday.year == year]


def get_next_bank_holiday(from_date=None):
    """
    Get the next bank holiday from a given date (or today if not specified).
    
    Args:
        from_date (date, optional): Date to search from. Defaults to today.
        
    Returns:
        date or None: The next bank holiday date, or None if none found
        
    Example:
        >>> from datetime import date
        >>> get_next_bank_holiday(date(2025, 1, 15))
        date(2025, 4, 18)  # Good Friday
    """
    if from_date is None:
        from_date = date.today()
    
    future_holidays = [holiday for holiday in UK_BANK_HOLIDAYS if holiday > from_date]
    return min(future_holidays) if future_holidays else None