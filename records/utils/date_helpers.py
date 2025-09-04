from datetime import date
from django.utils import timezone


def get_month_date_range(year, month):
    """
    Get start and end dates for a given month/year.
    
    Args:
        year (int): The year
        month (int): The month (1-12)
        
    Returns:
        tuple: (start_date, end_date) where end_date is the start of the next month
        
    Example:
        start, end = get_month_date_range(2025, 9)
        # Returns (date(2025, 9, 1), date(2025, 10, 1))
    """
    try:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        return start_date, end_date
    except ValueError:
        # Invalid month/year, return current month
        today = timezone.now().date()
        return get_month_date_range(today.year, today.month)


def get_month_navigation(month, year):
    """
    Get previous and next month/year for navigation.
    Does not allow navigation beyond current month.
    
    Args:
        month (int): Current month (1-12)
        year (int): Current year
        
    Returns:
        tuple: (prev_month, prev_year, next_month, next_year, can_go_next)
        
    Example:
        prev_m, prev_y, next_m, next_y, can_next = get_month_navigation(1, 2025)
        # Returns (12, 2024, 2, 2025, True/False)
    """
    today = timezone.now().date()
    
    # Previous month
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    
    # Next month    
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    
    # Check if we can go to next month (don't allow beyond current month)
    can_go_next = (next_year < today.year) or (next_year == today.year and next_month <= today.month)
        
    return prev_month, prev_year, next_month, next_year, can_go_next


def build_month_context(month, year):
    """
    Build common month navigation context for templates.
    
    Args:
        month (int): The month (1-12)
        year (int): The year
        
    Returns:
        dict: Context dictionary with month navigation data
        
    Example:
        context = build_month_context(9, 2025)
        # Returns dict with current_month, prev_month, etc.
    """
    today = timezone.now().date()
    current_month_start, _ = get_month_date_range(year, month)
    prev_month, prev_year, next_month, next_year, can_go_next = get_month_navigation(month, year)
    
    # Get available years based on actual block data (will be imported when used)
    from ..models import TimeBlock
    available_years = []
    block_years = TimeBlock.objects.dates('date', 'year')
    if block_years:
        available_years = [d.year for d in block_years]
        # Ensure current year is included
        if today.year not in available_years:
            available_years.append(today.year)
        # Only include years up to current year
        available_years = [y for y in available_years if y <= today.year]
        available_years.sort()
    else:
        # If no blocks exist yet, at least show current year
        available_years = [today.year]
    
    return {
        'current_month': current_month_start.strftime('%B %Y'),
        'current_month_num': month,
        'current_year': year,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'can_go_next': can_go_next,
        'is_current_month': (month == today.month and year == today.year),
        'available_years': available_years,
    }


def get_safe_month_year_from_request(request):
    """
    Safely extract month and year from request GET parameters.
    Returns current month/year if invalid values provided.
    
    Args:
        request: Django request object
        
    Returns:
        tuple: (month, year) as integers
    """
    today = timezone.now().date()
    
    try:
        month = int(request.GET.get('month', today.month))
        year = int(request.GET.get('year', today.year))
        
        # Validate month is between 1-12
        if not (1 <= month <= 12):
            month = today.month
            year = today.year
            
        # Validate year is reasonable (not too far in past/future)
        if not (2000 <= year <= 2100):
            month = today.month
            year = today.year
            
        return month, year
        
    except (ValueError, TypeError):
        # Invalid parameters, return current month/year
        return today.month, today.year