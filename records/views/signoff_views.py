"""Sign-off management views for monthly records and reports"""

import calendar

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from ..models import (
    MonthlyReportSignOff,
    MonthlySignOff,
    OnCallStaff,
    TimeBlock,
)
from ..utils.date_helpers import (
    build_month_context,
    get_month_date_range,
    get_safe_month_year_from_request,
)
from ..utils.decorators import require_staff_permission


@require_staff_permission
def signoff_management(request):
    """Sign-off management dashboard showing pending months for all staff"""

    # Get month/year from GET parameters with validation
    month, year = get_safe_month_year_from_request(request)

    # Calculate date range for selected month
    current_month_start, next_month_start = get_month_date_range(year, month)

    # Get all staff and their sign-off status for the selected month
    staff_signoff_status = []

    for staff in OnCallStaff.objects.all().select_related("user"):
        # Check if this staff member has any time blocks for the selected month
        time_blocks = TimeBlock.objects.filter(
            staff=staff, date__gte=current_month_start, date__lt=next_month_start
        )

        if time_blocks.exists():
            # Calculate totals for this month
            total_hours = sum(
                sum(entry.hours for entry in tb.time_entries.all())
                for tb in time_blocks.prefetch_related("time_entries")
            )
            total_claims = sum(tb.claim for tb in time_blocks if tb.claim)

            # Check sign-off status
            signoff = MonthlySignOff.get_signoff_for_month(staff, year, month)

            staff_signoff_status.append(
                {
                    "staff": staff,
                    "time_blocks_count": time_blocks.count(),
                    "total_hours": total_hours,
                    "total_claims": total_claims,
                    "is_signed_off": signoff is not None,
                    "signoff": signoff,
                }
            )

    # Build month context using utility function
    month_context = build_month_context(month, year)

    context = {
        "staff_signoff_status": staff_signoff_status,
        "selected_month": current_month_start,
        **month_context,
    }
    return render(request, "records/signoff_management.html", context)


@require_staff_permission
def signoff_month(request, staff_id, year, month):
    """Sign off a specific month for a specific staff member"""

    staff = get_object_or_404(OnCallStaff, id=staff_id)

    # Check if already signed off
    if MonthlySignOff.is_month_signed_off(staff, year, month):
        messages.warning(
            request,
            f"Month {month}/{year} for {staff.assignment_id} is already signed off.",
        )
        return redirect("signoff_management")

    # Check if staff has any time blocks for this month
    current_month_start, next_month_start = get_month_date_range(year, month)
    time_blocks = TimeBlock.objects.filter(
        staff=staff, date__gte=current_month_start, date__lt=next_month_start
    )

    if not time_blocks.exists():
        messages.error(
            request,
            f"No time blocks found for {staff.assignment_id} in {month}/{year}.",
        )
        return redirect("signoff_management")

    if request.method == "POST":
        notes = request.POST.get("notes", "")

        # Get the signing user's staff record
        try:
            signing_staff = OnCallStaff.objects.get(user=request.user)
        except OnCallStaff.DoesNotExist:
            messages.error(
                request, "You must be registered as on-call staff to sign off months."
            )
            return redirect("signoff_management")

        # Create the sign-off record
        MonthlySignOff.objects.create(
            staff=staff,
            year=year,
            month=month,
            signed_off_by=signing_staff,
            notes=notes,
        )

        messages.success(
            request,
            f"Successfully signed off {calendar.month_name[month]} {year} for {staff.assignment_id}.",
        )
        return redirect("signoff_management")

    # GET request - show confirmation page
    # Calculate totals for display
    time_blocks_with_totals = time_blocks.prefetch_related("time_entries")
    total_hours = sum(
        sum(entry.hours for entry in tb.time_entries.all())
        for tb in time_blocks_with_totals
    )
    total_claims = sum(tb.claim for tb in time_blocks if tb.claim)
    context = {
        "staff": staff,
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "time_blocks": time_blocks,
        "time_blocks_count": time_blocks.count(),
        "total_hours": total_hours,
        "total_claims": total_claims,
    }
    return render(request, "records/signoff_confirm.html", context)


@require_staff_permission
def unsignoff_month(request, signoff_id):
    """Remove a sign-off (admin only)"""

    signoff = get_object_or_404(MonthlySignOff, id=signoff_id)

    if request.method == "POST":
        staff_name = signoff.staff.assignment_id
        month_name = signoff.month_name
        year = signoff.year

        signoff.delete()

        messages.success(
            request,
            f"Successfully removed sign-off for {staff_name} - {month_name} {year}.",
        )
    else:
        messages.error(request, "Invalid request method.")

    return redirect("signoff_management")


@require_staff_permission
def signoff_report(request, year, month):
    """Sign off an entire monthly report for submission"""

    # Check if report is already signed off
    if MonthlyReportSignOff.is_report_signed_off(year, month):
        messages.warning(
            request, f"Monthly report for {month}/{year} is already signed off."
        )
        return redirect("monthly_report")

    # Calculate date range
    current_month_start, next_month_start = get_month_date_range(year, month)

    # Get all staff and their data for this month
    staff_reports = []
    for staff in OnCallStaff.objects.all().select_related("user"):
        time_blocks = TimeBlock.objects.filter(
            staff=staff, date__gte=current_month_start, date__lt=next_month_start
        ).prefetch_related("time_entries__task", "time_entries__work_mode")

        if time_blocks.exists():
            # Calculate totals by day type
            totals = {
                "Weekday": {"hours": 0.0, "claims": 0.0},
                "Saturday": {"hours": 0.0, "claims": 0.0},
                "Sunday": {"hours": 0.0, "claims": 0.0},
                "BankHoliday": {"hours": 0.0, "claims": 0.0},
            }

            for tb in time_blocks:
                block_hours = sum(entry.hours for entry in tb.time_entries.all())
                block_claims = float(tb.claim) if tb.claim else 0
                day_type_name = tb.day_type.name if tb.day_type else "Weekday"
                totals[day_type_name]["hours"] += block_hours
                totals[day_type_name]["claims"] += block_claims

            # Calculate grand totals
            total_hours = sum(t["hours"] for t in totals.values())
            total_claims = sum(t["claims"] for t in totals.values())

            staff_reports.append(
                {
                    "staff": staff,
                    "blocks": time_blocks,
                    "totals": totals,
                    "total_hours": total_hours,
                    "total_claims": total_claims,
                    "is_signed_off": MonthlySignOff.is_month_signed_off(
                        staff, year, month
                    ),
                }
            )

    if not staff_reports:
        messages.error(request, f"No time blocks found for {month}/{year}.")
        return redirect("monthly_report")

    # Check if all individual staff records are signed off
    unsigned_staff = [r for r in staff_reports if not r["is_signed_off"]]

    if request.method == "POST":
        notes = request.POST.get("notes", "")

        # Get the signing user's staff record
        try:
            signing_staff = OnCallStaff.objects.get(user=request.user)
        except OnCallStaff.DoesNotExist:
            messages.error(
                request, "You must be registered as on-call staff to sign off reports."
            )
            return redirect("monthly_report")

        # Calculate totals
        total_staff_count = len(staff_reports)
        grand_total_hours = sum(r["total_hours"] for r in staff_reports)
        grand_total_claims = sum(r["total_claims"] for r in staff_reports)

        # Create the report sign-off record
        MonthlyReportSignOff.objects.create(
            year=year,
            month=month,
            signed_off_by=signing_staff,
            notes=notes,
            total_staff_count=total_staff_count,
            total_hours=grand_total_hours,
            total_claims=grand_total_claims,
        )

        messages.success(
            request,
            f"Successfully signed off monthly report for {calendar.month_name[month]} {year}.",
        )
        return redirect("monthly_report")

    # GET request - show confirmation page
    grand_total_hours = sum(r["total_hours"] for r in staff_reports)
    grand_total_claims = sum(r["total_claims"] for r in staff_reports)
    signed_off_count = len(staff_reports) - len(unsigned_staff)

    context = {
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "staff_reports": staff_reports,
        "total_staff_count": len(staff_reports),
        "grand_total_hours": grand_total_hours,
        "grand_total_claims": grand_total_claims,
        "unsigned_staff": unsigned_staff,
        "signed_off_count": signed_off_count,
        "all_staff_signed_off": len(unsigned_staff) == 0,
    }
    return render(request, "records/report_signoff_confirm.html", context)


@require_staff_permission
def unsignoff_report(request, year, month):
    """Remove a report sign-off (admin only)"""

    report_signoff = get_object_or_404(MonthlyReportSignOff, year=year, month=month)

    if request.method == "POST":
        report_signoff.delete()

        messages.success(
            request,
            f"Successfully removed report sign-off for {calendar.month_name[month]} {year}.",
        )
    else:
        messages.error(request, "Invalid request method.")

    return redirect("monthly_report")