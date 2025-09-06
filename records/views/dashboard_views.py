"""Dashboard views for managing on-call records"""

from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from ..models import MonthlySignOff, OnCallStaff, TimeBlock
from ..utils.date_helpers import (
    build_month_context,
    get_month_date_range,
    get_safe_month_year_from_request,
)
from ..utils.decorators import require_oncall_staff, require_staff_permission


def get_dashboard_url_with_date(date_obj):
    """Helper function to build dashboard URL with month/year parameters"""
    return f"{reverse('dashboard')}?month={date_obj.month}&year={date_obj.year}"


@require_oncall_staff
def dashboard(request):
    """Dashboard showing user's time blocks for selected month"""
    staff = request.staff

    # Get month/year from GET parameters with validation
    month, year = get_safe_month_year_from_request(request)

    # Calculate date range for selected month
    current_month_start, next_month_start = get_month_date_range(year, month)

    time_blocks = (
        TimeBlock.objects.filter(
            staff=staff, date__gte=current_month_start, date__lt=next_month_start
        )
        .prefetch_related(
            "time_entries__task", "time_entries__work_mode", "assignments"
        )
        .order_by("-date")
    )

    # Add calculated totals to each block
    for tb in time_blocks:
        tb.calculated_hours = sum(entry.hours for entry in tb.time_entries.all())

    # Calculate totals
    total_hours = sum(
        sum(entry.hours for entry in tb.time_entries.all()) for tb in time_blocks
    )
    total_claims = sum(tb.claim for tb in time_blocks if tb.claim)

    # Build month context using utility function
    month_context = build_month_context(month, year)

    # Check if the current month is signed off
    month_signoff = MonthlySignOff.get_signoff_for_month(staff, year, month)

    # Combine with view-specific context
    context = {
        "staff": staff,
        "time_blocks": time_blocks,
        "total_hours": total_hours,
        "total_claims": total_claims,
        "month_signoff": month_signoff,
        "is_month_signed_off": month_signoff is not None,
        **month_context,  # Merge month navigation context
    }
    return render(request, "records/dashboard.html", context)


@require_staff_permission
def admin_user_dashboard(request, user_id):
    """Admin view to see a specific user's dashboard"""

    staff = get_object_or_404(OnCallStaff, user_id=user_id)

    # Get month/year from GET parameters with validation
    month, year = get_safe_month_year_from_request(request)

    # Calculate date range for selected month
    current_month_start, next_month_start = get_month_date_range(year, month)

    time_blocks = (
        TimeBlock.objects.filter(
            staff=staff, date__gte=current_month_start, date__lt=next_month_start
        )
        .prefetch_related("time_entries__task", "time_entries__work_mode")
        .order_by("-date")
    )

    # Add calculated totals to each block
    for tb in time_blocks:
        tb.calculated_hours = sum(entry.hours for entry in tb.time_entries.all())

    # Calculate totals
    total_hours = sum(
        sum(entry.hours for entry in tb.time_entries.all()) for tb in time_blocks
    )
    total_claims = sum(tb.claim for tb in time_blocks if tb.claim)

    # Build month context using utility function
    month_context = build_month_context(month, year)

    context = {
        "staff": staff,
        "time_blocks": time_blocks,
        "total_hours": total_hours,
        "total_claims": total_claims,
        "is_admin_view": True,
        **month_context,  # Merge month navigation context
    }
    return render(request, "records/admin_user_dashboard.html", context)