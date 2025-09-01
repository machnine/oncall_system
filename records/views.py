from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, date
from .models import OnCallStaff, Shift, TimeEntry, WorkMode, Task, Detail
from .forms import ShiftForm, TimeEntryForm


def get_dashboard_url_with_date(date_obj):
    """Helper function to build dashboard URL with month/year parameters"""
    return f"{reverse('dashboard')}?month={date_obj.month}&year={date_obj.year}"


@login_required
def dashboard(request):
    """Dashboard showing user's shifts for selected month"""
    try:
        staff = OnCallStaff.objects.get(user=request.user)
    except OnCallStaff.DoesNotExist:
        messages.error(request, 'You are not registered as on-call staff.')
        return redirect('admin:index')
    
    # Get month/year from GET parameters, default to current month
    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    
    # Calculate date range for selected month
    try:
        current_month_start = date(year, month, 1)
        if month == 12:
            next_month_start = date(year + 1, 1, 1)
        else:
            next_month_start = date(year, month + 1, 1)
    except ValueError:
        # Invalid month/year, default to current month
        current_month_start = today.replace(day=1)
        if today.month == 12:
            next_month_start = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month_start = today.replace(month=today.month + 1, day=1)
        month = today.month
        year = today.year
    
    shifts = Shift.objects.filter(
        staff=staff,
        date__gte=current_month_start,
        date__lt=next_month_start
    ).prefetch_related('time_entries__task', 'time_entries__work_mode').order_by('-date')
    
    # Add calculated totals to each shift
    for shift in shifts:
        shift.calculated_hours = sum(entry.hours for entry in shift.time_entries.all())
        shift.calculated_claims = sum(entry.claim for entry in shift.time_entries.all())
    
    # Calculate totals
    total_hours = sum(
        sum(entry.hours for entry in shift.time_entries.all()) 
        for shift in shifts
    )
    total_claims = sum(
        sum(entry.claim for entry in shift.time_entries.all()) 
        for shift in shifts
    )
    
    # Calculate previous/next month for navigation
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
        
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    
    # Generate available years based on actual shift data
    available_years = []
    shift_years = Shift.objects.dates('date', 'year')
    if shift_years:
        available_years = [d.year for d in shift_years]
    else:
        # If no shifts exist yet, at least show current year
        available_years = [today.year]
    
    context = {
        'staff': staff,
        'shifts': shifts,
        'total_hours': total_hours,
        'total_claims': total_claims,
        'current_month': current_month_start.strftime('%B %Y'),
        'current_month_num': month,
        'current_year': year,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'is_current_month': (month == today.month and year == today.year),
        'available_years': available_years,
    }
    return render(request, 'records/dashboard.html', context)


@login_required
def add_shift(request):
    """Add a new shift"""
    try:
        staff = OnCallStaff.objects.get(user=request.user)
    except OnCallStaff.DoesNotExist:
        messages.error(request, 'You are not registered as on-call staff.')
        return redirect('admin:index')
    
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            shift = form.save(commit=False)
            shift.staff = staff
            shift.save()
            messages.success(request, 'Shift created successfully!')
            return redirect(get_dashboard_url_with_date(shift.date))
    else:
        form = ShiftForm()
    
    return render(request, 'records/add_shift.html', {'form': form})


@login_required
def shift_detail(request, shift_id):
    """View and manage time entries for a specific shift"""
    try:
        staff = OnCallStaff.objects.get(user=request.user)
        shift = get_object_or_404(Shift, id=shift_id, staff=staff)
    except OnCallStaff.DoesNotExist:
        messages.error(request, 'You are not registered as on-call staff.')
        return redirect('admin:index')
    
    time_entries = shift.time_entries.all().order_by('time_started')
    total_hours = sum(entry.hours for entry in time_entries)
    total_claims = sum(entry.claim for entry in time_entries)
    
    context = {
        'shift': shift,
        'time_entries': time_entries,
        'total_hours': total_hours,
        'total_claims': total_claims,
    }
    return render(request, 'records/shift_detail.html', context)


@login_required
def add_time_entry(request, shift_id):
    """Add a time entry to a shift"""
    try:
        staff = OnCallStaff.objects.get(user=request.user)
        shift = get_object_or_404(Shift, id=shift_id, staff=staff)
    except OnCallStaff.DoesNotExist:
        messages.error(request, 'You are not registered as on-call staff.')
        return redirect('admin:index')
    
    if request.method == 'POST':
        form = TimeEntryForm(request.POST)
        if form.is_valid():
            time_entry = form.save(commit=False)
            time_entry.shift = shift
            time_entry.save()
            messages.success(request, 'Time entry added successfully!')
            return redirect('shift_detail', shift_id=shift.id)
    else:
        form = TimeEntryForm()
    
    context = {
        'form': form,
        'shift': shift,
    }
    return render(request, 'records/add_time_entry.html', context)


@login_required
def edit_time_entry(request, entry_id):
    """Edit a time entry"""
    try:
        staff = OnCallStaff.objects.get(user=request.user)
        time_entry = get_object_or_404(TimeEntry, id=entry_id, shift__staff=staff)
    except OnCallStaff.DoesNotExist:
        messages.error(request, 'You are not registered as on-call staff.')
        return redirect('admin:index')
    
    if request.method == 'POST':
        form = TimeEntryForm(request.POST, instance=time_entry)
        if form.is_valid():
            form.save()
            messages.success(request, 'Time entry updated successfully!')
            return redirect(get_dashboard_url_with_date(time_entry.shift.date))
    else:
        form = TimeEntryForm(instance=time_entry)
        # Pre-populate detail_text if entry has detail
        if time_entry.detail:
            form.fields['detail_text'].initial = time_entry.detail.text
    
    context = {
        'form': form,
        'time_entry': time_entry,
        'shift': time_entry.shift,
    }
    return render(request, 'records/edit_time_entry.html', context)


@login_required
def delete_time_entry(request, entry_id):
    """Delete a time entry"""
    try:
        staff = OnCallStaff.objects.get(user=request.user)
        time_entry = get_object_or_404(TimeEntry, id=entry_id, shift__staff=staff)
    except OnCallStaff.DoesNotExist:
        messages.error(request, 'You are not registered as on-call staff.')
        return redirect('admin:index')
    
    if request.method == 'POST':
        shift_date = time_entry.shift.date
        time_entry.delete()
        messages.success(request, 'Time entry deleted successfully!')
        return redirect(get_dashboard_url_with_date(shift_date))
    
    return render(request, 'records/confirm_delete_time_entry.html', {
        'time_entry': time_entry,
        'shift': time_entry.shift,
    })


@login_required
def edit_shift(request, shift_id):
    """Edit a shift"""
    try:
        staff = OnCallStaff.objects.get(user=request.user)
        shift = get_object_or_404(Shift, id=shift_id, staff=staff)
    except OnCallStaff.DoesNotExist:
        messages.error(request, 'You are not registered as on-call staff.')
        return redirect('admin:index')
    
    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            updated_shift = form.save()
            messages.success(request, 'Shift updated successfully!')
            return redirect(get_dashboard_url_with_date(updated_shift.date))
    else:
        form = ShiftForm(instance=shift)
    
    return render(request, 'records/edit_shift.html', {
        'form': form,
        'shift': shift,
    })


@login_required
def delete_shift(request, shift_id):
    """Delete a shift and all its time entries"""
    try:
        staff = OnCallStaff.objects.get(user=request.user)
        shift = get_object_or_404(Shift, id=shift_id, staff=staff)
    except OnCallStaff.DoesNotExist:
        messages.error(request, 'You are not registered as on-call staff.')
        return redirect('admin:index')
    
    if request.method == 'POST':
        shift_date = shift.date
        shift.delete()
        messages.success(request, 'Shift and all time entries deleted successfully!')
        return redirect(get_dashboard_url_with_date(shift_date))
    
    return render(request, 'records/confirm_delete_shift.html', {
        'shift': shift,
        'entry_count': shift.time_entries.count(),
    })


@login_required
def monthly_report(request):
    """Generate month-end claim report for all staff"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get month/year from GET parameters, default to current month
    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    
    # Calculate date range
    report_date = date(year, month, 1)
    if month == 12:
        next_month_start = date(year + 1, 1, 1)
    else:
        next_month_start = date(year, month + 1, 1)
    
    # Get all staff and their shifts for the month
    staff_reports = []
    for staff in OnCallStaff.objects.all().select_related('user'):
        shifts = Shift.objects.filter(
            staff=staff,
            date__gte=report_date,
            date__lt=next_month_start
        ).prefetch_related('time_entries__task', 'time_entries__work_mode')
        
        if shifts.exists():
            # Calculate totals by day type
            totals = {
                'Weekday': {'hours': 0, 'claims': 0},
                'Saturday': {'hours': 0, 'claims': 0},
                'Sunday': {'hours': 0, 'claims': 0},
                'BankHoliday': {'hours': 0, 'claims': 0},
            }
            
            for shift in shifts:
                shift_hours = sum(entry.hours for entry in shift.time_entries.all())
                shift_claims = sum(entry.claim for entry in shift.time_entries.all())
                totals[shift.day_type]['hours'] += shift_hours
                totals[shift.day_type]['claims'] += shift_claims
            
            # Calculate grand totals
            total_hours = sum(t['hours'] for t in totals.values())
            total_claims = sum(t['claims'] for t in totals.values())
            
            staff_reports.append({
                'staff': staff,
                'shifts': shifts,
                'totals': totals,
                'total_hours': total_hours,
                'total_claims': total_claims,
            })
    
    # Generate available months for dropdown
    first_shift = Shift.objects.order_by('date').first()
    available_months = []
    if first_shift:
        current_date = first_shift.date.replace(day=1)
        while current_date <= today:
            available_months.append(current_date)
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
    
    # Calculate previous/next month for navigation
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
        
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    
    # Generate available years based on actual shift data
    available_years = []
    shift_years = Shift.objects.dates('date', 'year')
    if shift_years:
        available_years = [d.year for d in shift_years]
    else:
        # If no shifts exist yet, at least show current year
        available_years = [today.year]
    
    context = {
        'staff_reports': staff_reports,
        'report_month': report_date,
        'available_months': available_months,
        'current_month': report_date.strftime('%B %Y'),
        'current_month_num': month,
        'current_year': year,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'available_years': available_years,
    }
    return render(request, 'records/monthly_report.html', context)


@login_required
def export_monthly_csv(request):
    """Export monthly report as CSV"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    import csv
    from django.http import HttpResponse
    
    # Get month/year from GET parameters, default to current month
    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    
    # Calculate date range for selected month
    try:
        report_date = date(year, month, 1)
        if month == 12:
            next_month_start = date(year + 1, 1, 1)
        else:
            next_month_start = date(year, month + 1, 1)
    except ValueError:
        # Invalid month/year, default to current month
        report_date = today.replace(day=1)
        if today.month == 12:
            next_month_start = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month_start = today.replace(month=today.month + 1, day=1)
    
    # Get all staff and their shifts for the month
    staff_reports = []
    for staff in OnCallStaff.objects.all().select_related('user'):
        shifts = Shift.objects.filter(
            staff=staff,
            date__gte=report_date,
            date__lt=next_month_start
        ).prefetch_related('time_entries__task', 'time_entries__work_mode')
        
        if shifts.exists():
            # Calculate totals by day type
            totals = {
                'Weekday': {'claims': 0},
                'Saturday': {'claims': 0},
                'Sunday': {'claims': 0},
                'BankHoliday': {'claims': 0},
            }
            
            for shift in shifts:
                shift_claims = sum(entry.claim for entry in shift.time_entries.all())
                totals[shift.day_type]['claims'] += shift_claims
            
            total_claims = sum(t['claims'] for t in totals.values())
            
            staff_reports.append({
                'staff': staff,
                'totals': totals,
                'total_claims': total_claims,
            })
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="oncall_report_{report_date.strftime("%Y_%m")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow(['Assignment ID', 'Name', 'Weekday', 'Saturday', 'Sunday', 'Bank Holiday', 'Total'])
    
    # Write data rows
    for staff_report in staff_reports:
        writer.writerow([
            staff_report['staff'].assignment_id,
            f"{staff_report['staff'].user.last_name}, {staff_report['staff'].user.first_name}",
            f"{staff_report['totals']['Weekday']['claims']:.2f}",
            f"{staff_report['totals']['Saturday']['claims']:.2f}",
            f"{staff_report['totals']['Sunday']['claims']:.2f}",
            f"{staff_report['totals']['BankHoliday']['claims']:.2f}",
            f"{staff_report['total_claims']:.2f}",
        ])
    
    # Write totals row
    if staff_reports:
        weekday_total = sum(report['totals']['Weekday']['claims'] for report in staff_reports)
        saturday_total = sum(report['totals']['Saturday']['claims'] for report in staff_reports)
        sunday_total = sum(report['totals']['Sunday']['claims'] for report in staff_reports)
        bh_total = sum(report['totals']['BankHoliday']['claims'] for report in staff_reports)
        grand_total = sum(report['total_claims'] for report in staff_reports)
        
        writer.writerow([])  # Empty row
        writer.writerow([
            'TOTALS', '',
            f"{weekday_total:.2f}",
            f"{saturday_total:.2f}",
            f"{sunday_total:.2f}",
            f"{bh_total:.2f}",
            f"{grand_total:.2f}",
        ])
    
    return response


@login_required
def admin_user_dashboard(request, user_id):
    """Admin view to see a specific user's dashboard"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    staff = get_object_or_404(OnCallStaff, user_id=user_id)
    
    # Get month/year from GET parameters, default to current month
    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    
    # Calculate date range for selected month
    try:
        current_month_start = date(year, month, 1)
        if month == 12:
            next_month_start = date(year + 1, 1, 1)
        else:
            next_month_start = date(year, month + 1, 1)
    except ValueError:
        # Invalid month/year, default to current month
        current_month_start = today.replace(day=1)
        if today.month == 12:
            next_month_start = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month_start = today.replace(month=today.month + 1, day=1)
        month = today.month
        year = today.year
    
    shifts = Shift.objects.filter(
        staff=staff,
        date__gte=current_month_start,
        date__lt=next_month_start
    ).prefetch_related('time_entries__task', 'time_entries__work_mode').order_by('-date')
    
    # Add calculated totals to each shift
    for shift in shifts:
        shift.calculated_hours = sum(entry.hours for entry in shift.time_entries.all())
        shift.calculated_claims = sum(entry.claim for entry in shift.time_entries.all())
    
    # Calculate totals
    total_hours = sum(
        sum(entry.hours for entry in shift.time_entries.all()) 
        for shift in shifts
    )
    total_claims = sum(
        sum(entry.claim for entry in shift.time_entries.all()) 
        for shift in shifts
    )
    
    # Calculate previous/next month for navigation
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
        
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    
    context = {
        'staff': staff,
        'shifts': shifts,
        'total_hours': total_hours,
        'total_claims': total_claims,
        'current_month': current_month_start.strftime('%B %Y'),
        'current_month_num': month,
        'current_year': year,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'is_current_month': (month == today.month and year == today.year),
        'is_admin_view': True,
    }
    return render(request, 'records/admin_user_dashboard.html', context)
