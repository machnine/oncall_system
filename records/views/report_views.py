"""Monthly report views for on-call records"""

import csv

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from ..models import OnCallStaff, TimeBlock
from ..utils.date_helpers import (
    build_month_context,
    get_month_date_range,
    get_safe_month_year_from_request,
)
from ..utils.decorators import require_staff_permission


@require_staff_permission
def monthly_report(request):
    """Generate month-end claim report for all staff"""

    # Get month/year from GET parameters with validation
    month, year = get_safe_month_year_from_request(request)

    # Calculate date range
    report_date, next_month_start = get_month_date_range(year, month)

    # Get all staff and their blocks for the month
    staff_reports = []
    for staff in OnCallStaff.objects.all().select_related("user"):
        time_blocks = TimeBlock.objects.filter(
            staff=staff, date__gte=report_date, date__lt=next_month_start
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
                }
            )

    # Generate available months for dropdown
    first_block = TimeBlock.objects.order_by("date").first()
    available_months = []
    if first_block:
        today = timezone.now().date()
        current_date = first_block.date.replace(day=1)
        while current_date <= today:
            available_months.append(current_date)
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

    # Import here to avoid circular imports
    from ..models import MonthlyReportSignOff, MonthlySignOff

    # Check if this report is signed off
    report_signoff = MonthlyReportSignOff.get_report_signoff(year, month)
    is_report_signed_off = report_signoff is not None

    # Calculate grand totals for the report
    grand_total_hours = sum(report["total_hours"] for report in staff_reports)
    grand_total_claims = sum(report["total_claims"] for report in staff_reports)

    # Check individual staff sign-off status
    staff_signoff_summary = None
    if staff_reports:
        all_staff_with_records = {report["staff"] for report in staff_reports}
        signed_off_staff = set()
        for staff in all_staff_with_records:
            if MonthlySignOff.is_month_signed_off(staff, year, month):
                signed_off_staff.add(staff)

        staff_signoff_summary = {
            "total_staff": len(all_staff_with_records),
            "signed_off_count": len(signed_off_staff),
            "pending_count": len(all_staff_with_records) - len(signed_off_staff),
            "all_signed_off": len(signed_off_staff) == len(all_staff_with_records),
        }

    # Build month context using utility function
    month_context = build_month_context(month, year)

    context = {
        "staff_reports": staff_reports,
        "report_month": report_date,
        "available_months": available_months,
        "report_signoff": report_signoff,
        "is_report_signed_off": is_report_signed_off,
        "grand_total_hours": grand_total_hours,
        "grand_total_claims": grand_total_claims,
        "staff_signoff_summary": staff_signoff_summary,
        **month_context,  # Merge month navigation context
    }
    return render(request, "records/monthly_report.html", context)


@require_staff_permission
def export_monthly_csv(request):
    """Export monthly report as CSV"""

    # Get month/year from GET parameters with validation
    month, year = get_safe_month_year_from_request(request)

    # Allow export regardless of sign-off status

    # Calculate date range for selected month
    report_date, next_month_start = get_month_date_range(year, month)

    # Get all staff and their blocks for the month
    staff_reports = []
    for staff in OnCallStaff.objects.all().select_related("user"):
        time_blocks = TimeBlock.objects.filter(
            staff=staff, date__gte=report_date, date__lt=next_month_start
        ).prefetch_related("time_entries__task", "time_entries__work_mode")

        if time_blocks.exists():
            # Calculate totals by day type
            totals = {
                "Weekday": {"claims": 0.0},
                "Saturday": {"claims": 0.0},
                "Sunday": {"claims": 0.0},
                "BankHoliday": {"claims": 0.0},
            }

            for tb in time_blocks:
                block_claims = float(tb.claim) if tb.claim else 0.0
                day_type_name = tb.day_type.name if tb.day_type else "Weekday"
                totals[day_type_name]["claims"] += block_claims

            total_claims = sum(t["claims"] for t in totals.values())

            staff_reports.append(
                {
                    "staff": staff,
                    "totals": totals,
                    "total_claims": total_claims,
                }
            )

    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="oncall_report_{report_date.strftime("%Y_%m")}.csv"'
    )

    writer = csv.writer(response)

    # Write header
    writer.writerow(
        [
            "Assignment ID",
            "Name",
            "Weekday",
            "Saturday",
            "Sunday",
            "Bank Holiday",
            "Total",
        ]
    )

    # Write data rows
    for staff_report in staff_reports:
        writer.writerow(
            [
                staff_report["staff"].assignment_id,
                f"{staff_report['staff'].user.last_name}, {staff_report['staff'].user.first_name}",
                f"{staff_report['totals']['Weekday']['claims']:.2f}",
                f"{staff_report['totals']['Saturday']['claims']:.2f}",
                f"{staff_report['totals']['Sunday']['claims']:.2f}",
                f"{staff_report['totals']['BankHoliday']['claims']:.2f}",
                f"{staff_report['total_claims']:.2f}",
            ]
        )

    # Write totals row
    if staff_reports:
        weekday_total = sum(
            report["totals"]["Weekday"]["claims"] for report in staff_reports
        )
        saturday_total = sum(
            report["totals"]["Saturday"]["claims"] for report in staff_reports
        )
        sunday_total = sum(
            report["totals"]["Sunday"]["claims"] for report in staff_reports
        )
        bh_total = sum(
            report["totals"]["BankHoliday"]["claims"] for report in staff_reports
        )
        grand_total = sum(report["total_claims"] for report in staff_reports)

        writer.writerow([])  # Empty row
        writer.writerow(
            [
                "TOTALS",
                "",
                f"{weekday_total:.2f}",
                f"{saturday_total:.2f}",
                f"{sunday_total:.2f}",
                f"{bh_total:.2f}",
                f"{grand_total:.2f}",
            ]
        )

    return response