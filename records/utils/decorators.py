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