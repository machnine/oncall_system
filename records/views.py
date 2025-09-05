from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import OnCallStaff, TimeBlock, TimeEntry, MonthlySignOff, MonthlyReportSignOff, RotaEntry, RotaShift
from .forms import TimeBlockForm, TimeBlockEditForm, TimeEntryForm
from .utils.decorators import require_oncall_staff, require_staff_permission, check_month_not_signed_off, check_timeblock_not_signed_off
from .utils.date_helpers import (
    get_month_date_range,
    build_month_context,
    build_rota_month_context,
    get_safe_month_year_from_request,
)


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


@require_oncall_staff
@check_timeblock_not_signed_off
def add_timeblock(request):
    """Add a new block"""
    staff = request.staff

    if request.method == "POST":
        form = TimeBlockForm(request.POST)
        if form.is_valid():
            time_block = form.save(commit=False)
            time_block.staff = staff
            # Call form.save() with commit=True to trigger assignment processing
            form.instance = time_block  # Update form instance with staff
            time_block = form.save(commit=True)
            messages.success(request, "Block created successfully!")
            return redirect(get_dashboard_url_with_date(time_block.date))
    else:
        form = TimeBlockForm()

    return render(request, "records/add_timeblock.html", {"form": form})


@require_oncall_staff
@check_month_not_signed_off
def add_time_entry(request, block_id):
    """Add a time entry to a block"""
    staff = request.staff
    time_block = get_object_or_404(TimeBlock, id=block_id, staff=staff)

    if request.method == "POST":
        form = TimeEntryForm(request.POST)
        if form.is_valid():
            time_entry = form.save(commit=False)
            time_entry.timeblock = time_block
            time_entry.save()
            messages.success(request, "Time entry added successfully!")
            return redirect(get_dashboard_url_with_date(time_block.date))
    else:
        form = TimeEntryForm()

    context = {
        "form": form,
        "time_block": time_block,
    }
    return render(request, "records/add_timeentry.html", context)


@require_oncall_staff
@check_month_not_signed_off
def edit_time_entry(request, entry_id):
    """Edit a time entry"""
    staff = request.staff
    time_entry = get_object_or_404(TimeEntry, id=entry_id, timeblock__staff=staff)

    if request.method == "POST":
        form = TimeEntryForm(request.POST, instance=time_entry)
        if form.is_valid():
            form.save()
            messages.success(request, "Time entry updated successfully!")
            return redirect(get_dashboard_url_with_date(time_entry.timeblock.date))
    else:
        form = TimeEntryForm(instance=time_entry)
        # Pre-populate detail_text if entry has detail
        if time_entry.detail:
            form.fields["detail_text"].initial = time_entry.detail.text

    context = {
        "form": form,
        "time_entry": time_entry,
        "time_block": time_entry.timeblock,
    }
    return render(request, "records/edit_timeentry.html", context)


@require_oncall_staff
@check_month_not_signed_off
def delete_time_entry(request, entry_id):
    """Delete a time entry"""
    staff = request.staff
    time_entry = get_object_or_404(TimeEntry, id=entry_id, timeblock__staff=staff)

    if request.method == "POST":
        block_date = time_entry.timeblock.date
        time_entry.delete()
        messages.success(request, "Time entry deleted successfully!")
        return redirect(get_dashboard_url_with_date(block_date))

    return render(
        request,
        "records/confirm_delete_timeentry.html",
        {
            "time_entry": time_entry,
            "time_block": time_entry.timeblock,
        },
    )


@require_oncall_staff
@check_month_not_signed_off
def edit_timeblock(request, block_id):
    """Edit a block"""
    staff = request.staff
    time_block = get_object_or_404(
        TimeBlock.objects.prefetch_related("assignments"), id=block_id, staff=staff
    )

    if request.method == "POST":
        form = TimeBlockEditForm(request.POST, instance=time_block)
        if form.is_valid():
            updated_block = form.save()
            messages.success(request, "Block updated successfully!")
            return redirect(get_dashboard_url_with_date(updated_block.date))
    else:
        form = TimeBlockEditForm(instance=time_block)

    return render(
        request,
        "records/edit_timeblock.html",
        {
            "form": form,
            "time_block": time_block,
        },
    )


@require_oncall_staff
@check_month_not_signed_off
def delete_timeblock(request, block_id):
    """Delete a block and all its time entries"""
    staff = request.staff
    time_block = get_object_or_404(TimeBlock, id=block_id, staff=staff)

    if request.method == "POST":
        block_date = time_block.date
        time_block.delete()
        messages.success(request, "Block and all time entries deleted successfully!")
        return redirect(get_dashboard_url_with_date(block_date))

    return render(
        request,
        "records/confirm_delete_timeblock.html",
        {
            "time_block": time_block,
            "entry_count": time_block.time_entries.count(),
        },
    )


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

    # Check if this report is signed off
    report_signoff = MonthlyReportSignOff.get_report_signoff(year, month)
    is_report_signed_off = report_signoff is not None
    
    # Calculate grand totals for the report
    grand_total_hours = sum(report['total_hours'] for report in staff_reports)
    grand_total_claims = sum(report['total_claims'] for report in staff_reports)
    
    # Check individual staff sign-off status
    staff_signoff_summary = None
    if staff_reports:
        all_staff_with_records = {report['staff'] for report in staff_reports}
        signed_off_staff = set()
        for staff in all_staff_with_records:
            if MonthlySignOff.is_month_signed_off(staff, year, month):
                signed_off_staff.add(staff)
        
        staff_signoff_summary = {
            'total_staff': len(all_staff_with_records),
            'signed_off_count': len(signed_off_staff),
            'pending_count': len(all_staff_with_records) - len(signed_off_staff),
            'all_signed_off': len(signed_off_staff) == len(all_staff_with_records)
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

    import csv
    from django.http import HttpResponse

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


@require_staff_permission
def signoff_management(request):
    """Sign-off management dashboard showing pending months for all staff"""
    
    # Get month/year from GET parameters with validation
    month, year = get_safe_month_year_from_request(request)
    
    # Calculate date range for selected month
    current_month_start, next_month_start = get_month_date_range(year, month)
    
    # Get all staff and their sign-off status for the selected month
    staff_signoff_status = []
    
    for staff in OnCallStaff.objects.all().select_related('user'):
        # Check if this staff member has any time blocks for the selected month
        time_blocks = TimeBlock.objects.filter(
            staff=staff,
            date__gte=current_month_start,
            date__lt=next_month_start
        )
        
        if time_blocks.exists():
            # Calculate totals for this month
            total_hours = sum(
                sum(entry.hours for entry in tb.time_entries.all()) 
                for tb in time_blocks.prefetch_related('time_entries')
            )
            total_claims = sum(tb.claim for tb in time_blocks if tb.claim)
            
            # Check sign-off status
            signoff = MonthlySignOff.get_signoff_for_month(staff, year, month)
            
            staff_signoff_status.append({
                'staff': staff,
                'time_blocks_count': time_blocks.count(),
                'total_hours': total_hours,
                'total_claims': total_claims,
                'is_signed_off': signoff is not None,
                'signoff': signoff,
            })
    
    # Build month context using utility function
    month_context = build_month_context(month, year)
    
    context = {
        'staff_signoff_status': staff_signoff_status,
        'selected_month': current_month_start,
        **month_context,
    }
    return render(request, 'records/signoff_management.html', context)


@require_staff_permission  
def signoff_month(request, staff_id, year, month):
    """Sign off a specific month for a specific staff member"""
    
    staff = get_object_or_404(OnCallStaff, id=staff_id)
    
    # Check if already signed off
    if MonthlySignOff.is_month_signed_off(staff, year, month):
        messages.warning(request, f'Month {month}/{year} for {staff.assignment_id} is already signed off.')
        return redirect('signoff_management')
    
    # Check if staff has any time blocks for this month
    current_month_start, next_month_start = get_month_date_range(year, month)
    time_blocks = TimeBlock.objects.filter(
        staff=staff,
        date__gte=current_month_start,
        date__lt=next_month_start
    )
    
    if not time_blocks.exists():
        messages.error(request, f'No time blocks found for {staff.assignment_id} in {month}/{year}.')
        return redirect('signoff_management')
    
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        
        # Get the signing user's staff record
        try:
            signing_staff = OnCallStaff.objects.get(user=request.user)
        except OnCallStaff.DoesNotExist:
            messages.error(request, 'You must be registered as on-call staff to sign off months.')
            return redirect('signoff_management')
        
        # Create the sign-off record
        MonthlySignOff.objects.create(
            staff=staff,
            year=year,
            month=month,
            signed_off_by=signing_staff,
            notes=notes
        )
        
        from calendar import month_name
        messages.success(
            request, 
            f'Successfully signed off {month_name[month]} {year} for {staff.assignment_id}.'
        )
        return redirect('signoff_management')
    
    # GET request - show confirmation page
    # Calculate totals for display
    time_blocks_with_totals = time_blocks.prefetch_related('time_entries')
    total_hours = sum(
        sum(entry.hours for entry in tb.time_entries.all()) 
        for tb in time_blocks_with_totals
    )
    total_claims = sum(tb.claim for tb in time_blocks if tb.claim)
    
    from calendar import month_name
    context = {
        'staff': staff,
        'year': year,
        'month': month,
        'month_name': month_name[month],
        'time_blocks': time_blocks,
        'time_blocks_count': time_blocks.count(),
        'total_hours': total_hours,
        'total_claims': total_claims,
    }
    return render(request, 'records/signoff_confirm.html', context)


@require_staff_permission
def unsignoff_month(request, signoff_id):
    """Remove a sign-off (admin only)"""
    
    signoff = get_object_or_404(MonthlySignOff, id=signoff_id)
    
    if request.method == 'POST':
        staff_name = signoff.staff.assignment_id
        month_name = signoff.month_name
        year = signoff.year
        
        signoff.delete()
        
        messages.success(
            request,
            f'Successfully removed sign-off for {staff_name} - {month_name} {year}.'
        )
    else:
        messages.error(request, 'Invalid request method.')
    
    return redirect('signoff_management')


@require_staff_permission
def signoff_report(request, year, month):
    """Sign off an entire monthly report for submission"""
    
    # Check if report is already signed off
    if MonthlyReportSignOff.is_report_signed_off(year, month):
        messages.warning(request, f'Monthly report for {month}/{year} is already signed off.')
        return redirect('monthly_report')
    
    # Calculate date range
    current_month_start, next_month_start = get_month_date_range(year, month)
    
    # Get all staff and their data for this month
    staff_reports = []
    for staff in OnCallStaff.objects.all().select_related('user'):
        time_blocks = TimeBlock.objects.filter(
            staff=staff,
            date__gte=current_month_start,
            date__lt=next_month_start
        ).prefetch_related('time_entries__task', 'time_entries__work_mode')
        
        if time_blocks.exists():
            # Calculate totals by day type
            totals = {
                'Weekday': {'hours': 0.0, 'claims': 0.0},
                'Saturday': {'hours': 0.0, 'claims': 0.0},
                'Sunday': {'hours': 0.0, 'claims': 0.0},
                'BankHoliday': {'hours': 0.0, 'claims': 0.0},
            }
            
            for tb in time_blocks:
                block_hours = sum(entry.hours for entry in tb.time_entries.all())
                block_claims = float(tb.claim) if tb.claim else 0
                day_type_name = tb.day_type.name if tb.day_type else 'Weekday'
                totals[day_type_name]['hours'] += block_hours
                totals[day_type_name]['claims'] += block_claims
            
            # Calculate grand totals
            total_hours = sum(t['hours'] for t in totals.values())
            total_claims = sum(t['claims'] for t in totals.values())
            
            staff_reports.append({
                'staff': staff,
                'blocks': time_blocks,
                'totals': totals,
                'total_hours': total_hours,
                'total_claims': total_claims,
                'is_signed_off': MonthlySignOff.is_month_signed_off(staff, year, month)
            })
    
    if not staff_reports:
        messages.error(request, f'No time blocks found for {month}/{year}.')
        return redirect('monthly_report')
    
    # Check if all individual staff records are signed off
    unsigned_staff = [r for r in staff_reports if not r['is_signed_off']]
    
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        
        # Get the signing user's staff record
        try:
            signing_staff = OnCallStaff.objects.get(user=request.user)
        except OnCallStaff.DoesNotExist:
            messages.error(request, 'You must be registered as on-call staff to sign off reports.')
            return redirect('monthly_report')
        
        # Calculate totals
        total_staff_count = len(staff_reports)
        grand_total_hours = sum(r['total_hours'] for r in staff_reports)
        grand_total_claims = sum(r['total_claims'] for r in staff_reports)
        
        # Create the report sign-off record
        MonthlyReportSignOff.objects.create(
            year=year,
            month=month,
            signed_off_by=signing_staff,
            notes=notes,
            total_staff_count=total_staff_count,
            total_hours=grand_total_hours,
            total_claims=grand_total_claims
        )
        
        from calendar import month_name
        messages.success(
            request, 
            f'Successfully signed off monthly report for {month_name[month]} {year}.'
        )
        return redirect('monthly_report')
    
    # GET request - show confirmation page
    grand_total_hours = sum(r['total_hours'] for r in staff_reports)
    grand_total_claims = sum(r['total_claims'] for r in staff_reports)
    signed_off_count = len(staff_reports) - len(unsigned_staff)
    
    from calendar import month_name
    context = {
        'year': year,
        'month': month,
        'month_name': month_name[month],
        'staff_reports': staff_reports,
        'total_staff_count': len(staff_reports),
        'grand_total_hours': grand_total_hours,
        'grand_total_claims': grand_total_claims,
        'unsigned_staff': unsigned_staff,
        'signed_off_count': signed_off_count,
        'all_staff_signed_off': len(unsigned_staff) == 0,
    }
    return render(request, 'records/report_signoff_confirm.html', context)


@require_staff_permission
def unsignoff_report(request, year, month):
    """Remove a report sign-off (admin only)"""
    
    report_signoff = get_object_or_404(MonthlyReportSignOff, year=year, month=month)
    
    if request.method == 'POST':
        from calendar import month_name
        report_signoff.delete()
        
        messages.success(
            request,
            f'Successfully removed report sign-off for {month_name[month]} {year}.'
        )
    else:
        messages.error(request, 'Invalid request method.')
    
    return redirect('monthly_report')


@require_staff_permission
def rota_calendar(request):
    """Display monthly rota calendar"""
    import calendar
    from datetime import date, timedelta
    
    # Get month/year from GET parameters with validation
    month, year = get_safe_month_year_from_request(request)
    
    # Calculate date range for selected month
    current_month_start, next_month_start = get_month_date_range(year, month)
    
    # Generate calendar for the month
    cal = calendar.monthcalendar(year, month)
    
    # Get all rota entries for this month
    rota_entries = RotaEntry.objects.filter(
        date__gte=current_month_start,
        date__lt=next_month_start
    ).prefetch_related('shifts__staff').order_by('date')
    
    # Create a dictionary for quick lookup of rota entries by date
    rota_by_date = {entry.date: entry for entry in rota_entries}
    
    # Build calendar data with rota information
    calendar_weeks = []
    for week in cal:
        week_data = []
        for day_num in week:
            if day_num == 0:
                # Empty cell for days outside current month
                week_data.append(None)
            else:
                day_date = date(year, month, day_num)
                rota_entry = rota_by_date.get(day_date)
                
                # Get day info
                day_data = {
                    'date': day_date,
                    'day_num': day_num,
                    'is_today': day_date == date.today(),
                    'is_weekend': day_date.weekday() >= 5,
                    'rota_entry': rota_entry,
                    'shifts': rota_entry.get_shifts_by_type() if rota_entry else {'normal': [], 'nhsp': []},
                    'is_bank_holiday': False,
                }
                
                # Check if bank holiday
                if rota_entry:
                    day_data['is_bank_holiday'] = rota_entry.is_bank_holiday
                else:
                    from .utils.bank_holidays import is_bank_holiday
                    day_data['is_bank_holiday'] = is_bank_holiday(day_date)
                
                week_data.append(day_data)
        
        calendar_weeks.append(week_data)
    
    # Build month context for rota (allows future months)
    month_context = build_rota_month_context(month, year)
    
    # Get all staff for potential assignment
    all_staff = OnCallStaff.objects.all().select_related('user').order_by('assignment_id')
    
    context = {
        'calendar_weeks': calendar_weeks,
        'all_staff': all_staff,
        **month_context,
    }
    
    return render(request, 'records/rota_calendar.html', context)


@require_POST
@require_oncall_staff
def add_staff_to_rota(request):
    """AJAX endpoint to add staff to a specific rota day and seniority level"""
    try:
        data = json.loads(request.body)
        date_str = data.get('date')
        staff_id = data.get('staff_id')
        seniority_level = data.get('seniority_level')
        
        if not all([date_str, staff_id, seniority_level]):
            return JsonResponse({'error': 'Missing required data'}, status=400)
        
        # Parse date
        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get staff object
        staff = get_object_or_404(OnCallStaff, id=staff_id)
        
        # Get or create rota entry for this date
        rota_entry, created = RotaEntry.objects.get_or_create(
            date=date_obj,
            defaults={
                'shift_type': 'normal',
                'day_type': None
            }
        )
        
        # Check if staff already has a shift for this date and seniority level
        existing_shift = RotaShift.objects.filter(
            rota_entry=rota_entry,
            staff=staff,
            seniority_level=seniority_level
        ).first()
        
        if existing_shift:
            return JsonResponse({'error': 'Staff already assigned to this level on this date'}, status=400)
        
        # Create new shift
        shift = RotaShift.objects.create(
            rota_entry=rota_entry,
            staff=staff,
            seniority_level=seniority_level
        )
        
        # Return updated data for DOM update
        return JsonResponse({
            'success': True,
            'shift': {
                'id': shift.id,
                'staff_id': staff.assignment_id,
                'staff_name': staff.user.get_full_name(),
                'staff_color': staff.color,
                'seniority_level': seniority_level,
                'notes': shift.notes or ''
            },
            'rota_entry_id': rota_entry.id,
            'shift_type': rota_entry.shift_type
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@require_oncall_staff
def toggle_shift_type(request):
    """AJAX endpoint to toggle shift type between normal and NHSP"""
    try:
        data = json.loads(request.body)
        date_str = data.get('date')
        
        if not date_str:
            return JsonResponse({'error': 'Date is required'}, status=400)
        
        # Parse date
        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get or create rota entry for this date
        rota_entry, created = RotaEntry.objects.get_or_create(
            date=date_obj,
            defaults={
                'shift_type': 'normal',
                'day_type': None
            }
        )
        
        # Toggle shift type
        if rota_entry.shift_type == 'normal':
            rota_entry.shift_type = 'nhsp'
        else:
            rota_entry.shift_type = 'normal'
        rota_entry.save()
        
        return JsonResponse({
            'success': True,
            'shift_type': rota_entry.shift_type,
            'rota_entry_id': rota_entry.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@require_oncall_staff
def clear_day_staff(request):
    """AJAX endpoint to remove all staff from a specific date"""
    try:
        data = json.loads(request.body)
        date_str = data.get('date')
        seniority_level = data.get('seniority_level')  # Optional: clear specific level only
        
        if not date_str:
            return JsonResponse({'error': 'Date is required'}, status=400)
        
        # Parse date
        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get rota entry for this date
        try:
            rota_entry = RotaEntry.objects.get(date=date_obj)
        except RotaEntry.DoesNotExist:
            return JsonResponse({'error': 'No rota entry found for this date'}, status=404)
        
        # Delete shifts
        shifts_query = RotaShift.objects.filter(rota_entry=rota_entry)
        
        # If specific seniority level provided, filter by it
        if seniority_level:
            shifts_query = shifts_query.filter(seniority_level=seniority_level)
        
        deleted_count = shifts_query.count()
        shifts_query.delete()
        
        # If all shifts are deleted, optionally delete the rota entry
        if not rota_entry.shifts.exists():
            rota_entry.delete()
            rota_entry_id = None
        else:
            rota_entry_id = rota_entry.id
        
        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count,
            'rota_entry_id': rota_entry_id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
