from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def require_oncall_staff(view_func):
    """
    Decorator that ensures the user is registered as on-call staff.
    Adds the staff object to the request as request.staff.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        from ..models import OnCallStaff
        try:
            staff = OnCallStaff.objects.get(user=request.user)
            request.staff = staff  # Add staff to request for easy access
            return view_func(request, *args, **kwargs)
        except OnCallStaff.DoesNotExist:
            messages.error(request, 'You are not registered as on-call staff.')
            return redirect('admin:index')
    return wrapper


def require_staff_permission(view_func):
    """
    Decorator that ensures the user has staff permissions.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def check_month_not_signed_off(view_func):
    """
    Decorator that prevents editing of time blocks/entries in signed-off months.
    Works for views that have block_id or entry_id as parameter.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from ..models import TimeBlock, TimeEntry, MonthlySignOff
        
        # Get the date from the time block or time entry
        target_date = None
        staff = None
        
        if 'block_id' in kwargs:
            try:
                time_block = TimeBlock.objects.get(id=kwargs['block_id'])
                target_date = time_block.date
                staff = time_block.staff
            except TimeBlock.DoesNotExist:
                # Let the original view handle the 404
                return view_func(request, *args, **kwargs)
                
        elif 'entry_id' in kwargs:
            try:
                time_entry = TimeEntry.objects.select_related('timeblock').get(id=kwargs['entry_id'])
                target_date = time_entry.timeblock.date
                staff = time_entry.timeblock.staff
            except TimeEntry.DoesNotExist:
                # Let the original view handle the 404
                return view_func(request, *args, **kwargs)
        
        # If we couldn't determine the date, proceed with the original view
        if not target_date or not staff:
            return view_func(request, *args, **kwargs)
        
        # Check if the month is signed off
        if MonthlySignOff.is_month_signed_off(staff, target_date.year, target_date.month):
            signoff = MonthlySignOff.get_signoff_for_month(staff, target_date.year, target_date.month)
            messages.error(
                request, 
                f'Cannot edit records from {signoff.month_name} {signoff.year}. '
                f'This month was signed off by {signoff.signed_off_by.assignment_id} '
                f'on {signoff.signed_off_at.strftime("%d/%m/%Y")}.'
            )
            return redirect('dashboard')
        
        # Month is not signed off, proceed with the original view
        return view_func(request, *args, **kwargs)
    
    return wrapper


def check_timeblock_not_signed_off(view_func):
    """
    Decorator specifically for time block creation that checks if we're trying
    to create a block in a signed-off month.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from ..models import MonthlySignOff
        
        # Only check for POST requests (form submissions)
        if request.method == 'POST':
            date_str = request.POST.get('date')
            if date_str:
                try:
                    from datetime import datetime
                    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    staff = request.staff  # Assumes require_oncall_staff decorator is also applied
                    
                    if MonthlySignOff.is_month_signed_off(staff, target_date.year, target_date.month):
                        signoff = MonthlySignOff.get_signoff_for_month(staff, target_date.year, target_date.month)
                        messages.error(
                            request,
                            f'Cannot create records for {signoff.month_name} {signoff.year}. '
                            f'This month was signed off by {signoff.signed_off_by.assignment_id} '
                            f'on {signoff.signed_off_at.strftime("%d/%m/%Y")}.'
                        )
                        return redirect('dashboard')
                except (ValueError, TypeError):
                    # Invalid date format, let the form validation handle it
                    pass
        
        return view_func(request, *args, **kwargs)
    
    return wrapper