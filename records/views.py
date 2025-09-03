from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, date
from .models import OnCallStaff, Block, TimeEntry, WorkMode, Task, Detail
from .forms import BlockForm, BlockEditForm, TimeEntryForm
from .utils.decorators import require_oncall_staff, require_staff_permission
from .utils.date_helpers import get_month_date_range, build_month_context, get_safe_month_year_from_request


def get_dashboard_url_with_date(date_obj):
    """Helper function to build dashboard URL with month/year parameters"""
    return f"{reverse('dashboard')}?month={date_obj.month}&year={date_obj.year}"


@require_oncall_staff
def dashboard(request):
    """Dashboard showing user's blocks for selected month"""
    staff = request.staff
    
    # Get month/year from GET parameters with validation
    month, year = get_safe_month_year_from_request(request)
    
    # Calculate date range for selected month
    current_month_start, next_month_start = get_month_date_range(year, month)
    
    blocks = Block.objects.filter(
        staff=staff,
        date__gte=current_month_start,
        date__lt=next_month_start
    ).prefetch_related('time_entries__task', 'time_entries__work_mode').order_by('-date')
    
    # Add calculated totals to each block
    for block in blocks:
        block.calculated_hours = sum(entry.hours for entry in block.time_entries.all())
    
    # Calculate totals
    total_hours = sum(
        sum(entry.hours for entry in block.time_entries.all()) 
        for block in blocks
    )
    total_claims = sum(
        block.claim for block in blocks if block.claim
    )
    
    # Build month context using utility function
    month_context = build_month_context(month, year)
    
    # Combine with view-specific context
    context = {
        'staff': staff,
        'blocks': blocks,
        'total_hours': total_hours,
        'total_claims': total_claims,
        **month_context,  # Merge month navigation context
    }
    return render(request, 'records/dashboard.html', context)


@require_oncall_staff
def add_block(request):
    """Add a new block"""
    staff = request.staff
    
    if request.method == 'POST':
        form = BlockForm(request.POST)
        if form.is_valid():
            block = form.save(commit=False)
            block.staff = staff
            block.save()
            messages.success(request, 'Block created successfully!')
            return redirect(get_dashboard_url_with_date(block.date))
    else:
        form = BlockForm()
    
    return render(request, 'records/add_block.html', {'form': form})




@require_oncall_staff
def add_time_entry(request, block_id):
    """Add a time entry to a block"""
    staff = request.staff
    block = get_object_or_404(Block, id=block_id, staff=staff)
    
    if request.method == 'POST':
        form = TimeEntryForm(request.POST)
        if form.is_valid():
            time_entry = form.save(commit=False)
            time_entry.block = block
            time_entry.save()
            messages.success(request, 'Time entry added successfully!')
            return redirect(get_dashboard_url_with_date(block.date))
    else:
        form = TimeEntryForm()
    
    context = {
        'form': form,
        'time_block': block,
    }
    return render(request, 'records/add_time_entry.html', context)


@require_oncall_staff
def edit_time_entry(request, entry_id):
    """Edit a time entry"""
    staff = request.staff
    time_entry = get_object_or_404(TimeEntry, id=entry_id, block__staff=staff)
    
    if request.method == 'POST':
        form = TimeEntryForm(request.POST, instance=time_entry)
        if form.is_valid():
            form.save()
            messages.success(request, 'Time entry updated successfully!')
            return redirect(get_dashboard_url_with_date(time_entry.block.date))
    else:
        form = TimeEntryForm(instance=time_entry)
        # Pre-populate detail_text if entry has detail
        if time_entry.detail:
            form.fields['detail_text'].initial = time_entry.detail.text
    
    context = {
        'form': form,
        'time_entry': time_entry,
        'time_block': time_entry.block,
    }
    return render(request, 'records/edit_time_entry.html', context)


@require_oncall_staff
def delete_time_entry(request, entry_id):
    """Delete a time entry"""
    staff = request.staff
    time_entry = get_object_or_404(TimeEntry, id=entry_id, block__staff=staff)
    
    if request.method == 'POST':
        block_date = time_entry.block.date
        time_entry.delete()
        messages.success(request, 'Time entry deleted successfully!')
        return redirect(get_dashboard_url_with_date(block_date))
    
    return render(request, 'records/confirm_delete_time_entry.html', {
        'time_entry': time_entry,
        'time_block': time_entry.block,
    })


@require_oncall_staff
def edit_block(request, block_id):
    """Edit a block"""
    staff = request.staff
    block = get_object_or_404(Block, id=block_id, staff=staff)
    
    if request.method == 'POST':
        form = BlockEditForm(request.POST, instance=block)
        if form.is_valid():
            updated_block = form.save()
            messages.success(request, 'Block updated successfully!')
            return redirect(get_dashboard_url_with_date(updated_block.date))
    else:
        form = BlockEditForm(instance=block)
    
    return render(request, 'records/edit_block.html', {
        'form': form,
        'block': block,
    })


@require_oncall_staff
def delete_block(request, block_id):
    """Delete a block and all its time entries"""
    staff = request.staff
    block = get_object_or_404(Block, id=block_id, staff=staff)
    
    if request.method == 'POST':
        block_date = block.date
        block.delete()
        messages.success(request, 'Block and all time entries deleted successfully!')
        return redirect(get_dashboard_url_with_date(block_date))
    
    return render(request, 'records/confirm_delete_block.html', {
        'time_block': block,
        'entry_count': block.time_entries.count(),
    })


@require_staff_permission
def monthly_report(request):
    """Generate month-end claim report for all staff"""
    
    # Get month/year from GET parameters with validation
    month, year = get_safe_month_year_from_request(request)
    
    # Calculate date range
    report_date, next_month_start = get_month_date_range(year, month)
    
    # Get all staff and their blocks for the month
    staff_reports = []
    for staff in OnCallStaff.objects.all().select_related('user'):
        blocks = Block.objects.filter(
            staff=staff,
            date__gte=report_date,
            date__lt=next_month_start
        ).prefetch_related('time_entries__task', 'time_entries__work_mode')
        
        if blocks.exists():
            # Calculate totals by day type
            totals = {
                'Weekday': {'hours': 0, 'claims': 0},
                'Saturday': {'hours': 0, 'claims': 0},
                'Sunday': {'hours': 0, 'claims': 0},
                'BankHoliday': {'hours': 0, 'claims': 0},
            }
            
            for block in blocks:
                block_hours = sum(entry.hours for entry in block.time_entries.all())
                block_claims = block.claim if block.claim else 0
                totals[block.day_type]['hours'] += block_hours
                totals[block.day_type]['claims'] += block_claims
            
            # Calculate grand totals
            total_hours = sum(t['hours'] for t in totals.values())
            total_claims = sum(t['claims'] for t in totals.values())
            
            staff_reports.append({
                'staff': staff,
                'blocks': blocks,
                'totals': totals,
                'total_hours': total_hours,
                'total_claims': total_claims,
            })
    
    # Generate available months for dropdown
    first_block = Block.objects.order_by('date').first()
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
    
    # Build month context using utility function
    month_context = build_month_context(month, year)
    
    context = {
        'staff_reports': staff_reports,
        'report_month': report_date,
        'available_months': available_months,
        **month_context,  # Merge month navigation context
    }
    return render(request, 'records/monthly_report.html', context)


@require_staff_permission
def export_monthly_csv(request):
    """Export monthly report as CSV"""
    
    import csv
    from django.http import HttpResponse
    
    # Get month/year from GET parameters with validation
    month, year = get_safe_month_year_from_request(request)
    
    # Calculate date range for selected month
    report_date, next_month_start = get_month_date_range(year, month)
    
    # Get all staff and their blocks for the month
    staff_reports = []
    for staff in OnCallStaff.objects.all().select_related('user'):
        blocks = Block.objects.filter(
            staff=staff,
            date__gte=report_date,
            date__lt=next_month_start
        ).prefetch_related('time_entries__task', 'time_entries__work_mode')
        
        if blocks.exists():
            # Calculate totals by day type
            totals = {
                'Weekday': {'claims': 0},
                'Saturday': {'claims': 0},
                'Sunday': {'claims': 0},
                'BankHoliday': {'claims': 0},
            }
            
            for block in blocks:
                block_claims = block.claim if block.claim else 0
                totals[block.day_type]['claims'] += block_claims
            
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


@require_staff_permission
def admin_user_dashboard(request, user_id):
    """Admin view to see a specific user's dashboard"""
    
    staff = get_object_or_404(OnCallStaff, user_id=user_id)
    
    # Get month/year from GET parameters with validation
    month, year = get_safe_month_year_from_request(request)
    
    # Calculate date range for selected month
    current_month_start, next_month_start = get_month_date_range(year, month)
    
    blocks = Block.objects.filter(
        staff=staff,
        date__gte=current_month_start,
        date__lt=next_month_start
    ).prefetch_related('time_entries__task', 'time_entries__work_mode').order_by('-date')
    
    # Add calculated totals to each block
    for block in blocks:
        block.calculated_hours = sum(entry.hours for entry in block.time_entries.all())
    
    # Calculate totals
    total_hours = sum(
        sum(entry.hours for entry in block.time_entries.all()) 
        for block in blocks
    )
    total_claims = sum(
        block.claim for block in blocks if block.claim
    )
    
    # Build month context using utility function
    month_context = build_month_context(month, year)
    
    context = {
        'staff': staff,
        'blocks': blocks,
        'total_hours': total_hours,
        'total_claims': total_claims,
        'is_admin_view': True,
        **month_context,  # Merge month navigation context
    }
    return render(request, 'records/admin_user_dashboard.html', context)
