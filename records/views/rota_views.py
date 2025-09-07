"""Rota management views for scheduling on-call staff"""

import calendar
import json
from collections import defaultdict
from datetime import date, datetime, timedelta

from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from ..models import BankHoliday, OnCallStaff, RotaEntry, RotaShift
from ..utils.date_helpers import (
    build_rota_month_context,
    get_month_date_range,
    get_safe_month_year_from_request,
)
from ..utils.decorators import require_oncall_staff, require_staff_permission


@require_staff_permission
def rota_calendar(request):
    """Display monthly rota calendar"""
    # Get month/year from GET parameters with validation
    month, year = get_safe_month_year_from_request(request)

    # Calculate date range for selected month
    current_month_start, next_month_start = get_month_date_range(year, month)

    # Generate calendar for the month
    cal = calendar.monthcalendar(year, month)

    # Get all rota entries for this month
    rota_entries = (
        RotaEntry.objects.filter(
            date__gte=current_month_start, date__lt=next_month_start
        )
        .prefetch_related("shifts__staff")
        .order_by("date")
    )

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
                    "date": day_date,
                    "day_num": day_num,
                    "is_today": day_date == date.today(),
                    "is_weekend": day_date.weekday() >= 5,
                    "rota_entry": rota_entry,
                    "shifts": rota_entry.get_shifts_by_type()
                    if rota_entry
                    else {"normal": [], "nhsp": []},
                    "is_bank_holiday": False,
                }

                # Check if bank holiday
                if rota_entry:
                    day_data["is_bank_holiday"] = rota_entry.is_bank_holiday
                else:
                    day_data["is_bank_holiday"] = BankHoliday.is_bank_holiday(day_date)

                week_data.append(day_data)

        calendar_weeks.append(week_data)

    # Build month context for rota (allows future months)
    month_context = build_rota_month_context(month, year)

    # Get all staff for potential assignment, grouped by seniority level
    all_staff = (
        OnCallStaff.objects.all()
        .select_related("user")
        .order_by("seniority_level", "assignment_id")
    )

    # Group staff by seniority level for the context menu
    staff_by_seniority = {"trainee": [], "oncall": [], "senior": []}

    for staff in all_staff:
        if staff.seniority_level in staff_by_seniority:
            staff_by_seniority[staff.seniority_level].append(staff)

    context = {
        "calendar_weeks": calendar_weeks,
        "all_staff": all_staff,
        "staff_by_seniority": staff_by_seniority,
        **month_context,
    }

    return render(request, "records/rota_calendar.html", context)


@require_POST
@require_oncall_staff
def add_staff_to_rota(request):
    """AJAX endpoint to add staff to a specific rota day and seniority level"""
    try:
        data = json.loads(request.body)
        date_str = data.get("date")
        staff_id = data.get("staff_id")
        seniority_level = data.get("seniority_level")

        if not all([date_str, staff_id, seniority_level]):
            return JsonResponse({"error": "Missing required data"}, status=400)

        # Parse date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Get staff object
        staff = get_object_or_404(OnCallStaff, id=staff_id)

        # Get or create rota entry for this date
        rota_entry, created = RotaEntry.objects.get_or_create(
            date=date_obj, defaults={"shift_type": "normal"}
        )

        # Check if staff already has a shift for this date and seniority level
        existing_shift = RotaShift.objects.filter(
            rota_entry=rota_entry, staff=staff, seniority_level=seniority_level
        ).first()

        if existing_shift:
            return JsonResponse(
                {"error": "Staff already assigned to this level on this date"},
                status=400,
            )

        # Create new shift
        shift = RotaShift.objects.create(
            rota_entry=rota_entry, staff=staff, seniority_level=seniority_level
        )

        # Return updated data for DOM update
        return JsonResponse(
            {
                "success": True,
                "shift": {
                    "id": shift.id,
                    "staff_id": staff.assignment_id,
                    "staff_name": staff.user.get_full_name(),
                    "staff_color": staff.color,
                    "seniority_level": seniority_level,
                    "notes": shift.notes or "",
                },
                "rota_entry_id": rota_entry.id,
                "shift_type": rota_entry.shift_type,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@require_oncall_staff
def toggle_shift_type(request):
    """AJAX endpoint to toggle shift type between normal and NHSP"""
    try:
        data = json.loads(request.body)
        date_str = data.get("date")

        if not date_str:
            return JsonResponse({"error": "Date is required"}, status=400)

        # Parse date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Get or create rota entry for this date
        rota_entry, created = RotaEntry.objects.get_or_create(
            date=date_obj, defaults={"shift_type": "normal"}
        )

        # Toggle shift type (handle NULL values by treating them as 'normal')
        current_type = rota_entry.shift_type or "normal"
        if current_type == "normal":
            rota_entry.shift_type = "nhsp"
        else:
            rota_entry.shift_type = "normal"
        rota_entry.save()

        return JsonResponse(
            {
                "success": True,
                "shift_type": rota_entry.shift_type,
                "rota_entry_id": rota_entry.id,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@require_oncall_staff
def clear_day_staff(request):
    """AJAX endpoint to remove all staff from a specific date"""
    try:
        data = json.loads(request.body)
        date_str = data.get("date")
        seniority_level = data.get(
            "seniority_level"
        )  # Optional: clear specific level only

        if not date_str:
            return JsonResponse({"error": "Date is required"}, status=400)

        # Parse date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Get rota entry for this date
        try:
            rota_entry = RotaEntry.objects.get(date=date_obj)
        except RotaEntry.DoesNotExist:
            return JsonResponse(
                {"error": "No rota entry found for this date"}, status=404
            )

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

        return JsonResponse(
            {
                "success": True,
                "deleted_count": deleted_count,
                "rota_entry_id": rota_entry_id,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@require_oncall_staff
def create_rota_entry(request):
    """AJAX endpoint to create a RotaEntry for a specific date"""
    try:
        data = json.loads(request.body)
        date_str = data.get("date")

        if not date_str:
            return JsonResponse({"error": "Date is required"}, status=400)

        # Parse date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Get or create rota entry for this date
        rota_entry, created = RotaEntry.objects.get_or_create(
            date=date_obj, defaults={"shift_type": "normal"}
        )

        return JsonResponse(
            {
                "success": True,
                "shift_type": rota_entry.shift_type,
                "rota_entry_id": rota_entry.id,
                "created": created,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
@require_oncall_staff
def remove_staff_from_rota(request):
    """AJAX endpoint to remove a specific staff member from rota"""
    try:
        data = json.loads(request.body)
        shift_id = data.get("shift_id")

        if not shift_id:
            return JsonResponse({"error": "Shift ID is required"}, status=400)

        # Get the shift
        shift = get_object_or_404(RotaShift, id=shift_id)
        rota_entry = shift.rota_entry

        # Delete the shift
        shift.delete()

        # Check if this was the last shift for this rota entry
        remaining_shifts = RotaShift.objects.filter(rota_entry=rota_entry).count()

        response_data = {"success": True, "remaining_shifts": remaining_shifts}

        # If no shifts remain, optionally delete the rota entry
        if remaining_shifts == 0:
            rota_entry.delete()
            response_data["rota_entry_deleted"] = True
        else:
            response_data["rota_entry_deleted"] = False

        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_staff_permission
def rota_statistics(request):
    """Display comprehensive rota statistics by period and day type"""
    # Get period from GET parameters (default to current year)
    period_type = request.GET.get('period', 'yearly')  # yearly, quarterly, monthly
    year = int(request.GET.get('year', datetime.now().year))
    quarter = request.GET.get('quarter', '1')
    month = request.GET.get('month', '1')
    
    # Build date filter based on period
    date_filters = {}
    period_label = ""
    
    if period_type == 'monthly':
        month = int(month)
        date_filters['rota_entry__date__year'] = year
        date_filters['rota_entry__date__month'] = month
        period_label = f"{calendar.month_name[month]} {year}"
        
    elif period_type == 'quarterly':
        quarter = int(quarter)
        quarter_months = {
            1: [1, 2, 3],
            2: [4, 5, 6], 
            3: [7, 8, 9],
            4: [10, 11, 12]
        }
        date_filters['rota_entry__date__year'] = year
        date_filters['rota_entry__date__month__in'] = quarter_months[quarter]
        period_label = f"Q{quarter} {year}"
        
    else:  # yearly
        date_filters['rota_entry__date__year'] = year
        period_label = f"Year {year}"

    # Get all rota shifts for the period with related data
    shifts = (
        RotaShift.objects
        .filter(**date_filters)
        .select_related('staff__user', 'rota_entry')
        .order_by('rota_entry__date')
    )
    
    # Get all unique staff who worked during this period
    staff_stats = defaultdict(lambda: {
        'staff': None,
        'total_shifts': 0,
        'weekday_shifts': 0,
        'saturday_shifts': 0,
        'sunday_shifts': 0,
        'bank_holiday_shifts': 0,
        'normal_shifts': 0,
        'nhsp_shifts': 0,
        'seniority_breakdown': {'trainee': 0, 'oncall': 0, 'senior': 0}
    })
    
    # Overall statistics
    overall_stats = {
        'total_shifts': 0,
        'total_days_covered': 0,
        'weekday_shifts': 0,
        'saturday_shifts': 0,
        'sunday_shifts': 0,
        'bank_holiday_shifts': 0,
        'normal_shifts': 0,
        'nhsp_shifts': 0,
        'staff_count': 0
    }
    
    # Day type breakdown
    day_type_stats = defaultdict(int)
    shift_type_stats = defaultdict(int)
    seniority_stats = defaultdict(int)
    
    # Track unique dates to count days covered
    unique_dates = set()
    
    # Process each shift
    for shift in shifts:
        staff_id = shift.staff.id
        rota_entry = shift.rota_entry
        
        # Initialize staff record if first time seeing them
        if staff_stats[staff_id]['staff'] is None:
            staff_stats[staff_id]['staff'] = shift.staff
        
        # Track unique dates
        unique_dates.add(rota_entry.date)
        
        # Determine day type
        day_type = rota_entry.day_type  # Uses the property from model
        
        # Update staff statistics
        staff_stats[staff_id]['total_shifts'] += 1
        staff_stats[staff_id]['seniority_breakdown'][shift.seniority_level] += 1
        
        if day_type == 'Weekday':
            staff_stats[staff_id]['weekday_shifts'] += 1
        elif day_type == 'Saturday':
            staff_stats[staff_id]['saturday_shifts'] += 1
        elif day_type == 'Sunday':
            staff_stats[staff_id]['sunday_shifts'] += 1
        elif day_type == 'BankHoliday':
            staff_stats[staff_id]['bank_holiday_shifts'] += 1
            
        if rota_entry.shift_type == 'nhsp':
            staff_stats[staff_id]['nhsp_shifts'] += 1
        else:
            staff_stats[staff_id]['normal_shifts'] += 1
            
        # Update overall statistics
        overall_stats['total_shifts'] += 1
        day_type_stats[day_type] += 1
        shift_type_stats[rota_entry.shift_type] += 1
        seniority_stats[shift.seniority_level] += 1

    # Finalize overall stats
    overall_stats['total_days_covered'] = len(unique_dates)
    overall_stats['weekday_shifts'] = day_type_stats['Weekday']
    overall_stats['saturday_shifts'] = day_type_stats['Saturday']
    overall_stats['sunday_shifts'] = day_type_stats['Sunday']
    overall_stats['bank_holiday_shifts'] = day_type_stats['BankHoliday']
    overall_stats['normal_shifts'] = shift_type_stats.get('normal', 0)
    overall_stats['nhsp_shifts'] = shift_type_stats.get('nhsp', 0)
    overall_stats['staff_count'] = len(staff_stats)
    
    # Convert staff_stats to sorted list
    staff_list = sorted(
        staff_stats.values(), 
        key=lambda x: x['total_shifts'], 
        reverse=True
    )
    
    # Create separate lists for each seniority level (only if they have data)
    trainee_staff = [s for s in staff_list if s['seniority_breakdown']['trainee'] > 0]
    oncall_staff = [s for s in staff_list if s['seniority_breakdown']['oncall'] > 0] 
    senior_staff = [s for s in staff_list if s['seniority_breakdown']['senior'] > 0]
    
    # Bank Holiday Analysis - Last 5 Years
    five_years_ago = datetime.now().date() - timedelta(days=5*365)
    
    # Get all bank holiday shifts from the last 5 years
    bank_holiday_shifts = (
        RotaShift.objects
        .filter(
            rota_entry__date__gte=five_years_ago,
            rota_entry__date__lte=datetime.now().date()
        )
        .select_related('staff__user', 'rota_entry')
        .order_by('rota_entry__date')
    )
    
    # Filter only shifts that occurred on bank holidays
    bank_holiday_rota_shifts = []
    for shift in bank_holiday_shifts:
        if BankHoliday.is_bank_holiday(shift.rota_entry.date):
            bank_holiday_rota_shifts.append(shift)
    
    # Get all unique bank holidays from the last 5 years with shifts
    bank_holidays_with_shifts = set()
    for shift in bank_holiday_rota_shifts:
        try:
            bank_holiday = BankHoliday.objects.get(date=shift.rota_entry.date)
            bank_holidays_with_shifts.add(bank_holiday)
        except BankHoliday.DoesNotExist:
            pass
    
    # Sort bank holidays by date (most recent first)
    sorted_bank_holidays = sorted(bank_holidays_with_shifts, key=lambda x: x.date, reverse=True)
    
    # Build staff bank holiday statistics
    staff_bank_holiday_stats = defaultdict(lambda: {'staff': None, 'bank_holiday_counts': {}})
    
    for shift in bank_holiday_rota_shifts:
        staff_id = shift.staff.id
        if staff_bank_holiday_stats[staff_id]['staff'] is None:
            staff_bank_holiday_stats[staff_id]['staff'] = shift.staff
            
        # Find the bank holiday for this date
        try:
            bank_holiday = BankHoliday.objects.get(date=shift.rota_entry.date)
            bh_key = f"{bank_holiday.title}_{bank_holiday.date.year}"
            
            if bh_key not in staff_bank_holiday_stats[staff_id]['bank_holiday_counts']:
                staff_bank_holiday_stats[staff_id]['bank_holiday_counts'][bh_key] = {
                    'count': 0,
                    'bank_holiday': bank_holiday
                }
            staff_bank_holiday_stats[staff_id]['bank_holiday_counts'][bh_key]['count'] += 1
        except BankHoliday.DoesNotExist:
            pass
    
    # Create unique bank holiday columns (title + year combinations)
    bank_holiday_columns = []
    for bh in sorted_bank_holidays:
        bh_key = f"{bh.title}_{bh.date.year}"
        bank_holiday_columns.append({
            'key': bh_key,
            'title': bh.title,
            'year': bh.date.year,
            'date': bh.date,
            'display': f"{bh.title} {bh.date.year}"
        })
    
    # Convert to list and prepare data with column alignment
    bank_holiday_staff_list = []
    for data in staff_bank_holiday_stats.values():
        if data['staff'] is not None:
            # Create aligned columns for each staff member
            staff_row = {
                'staff': data['staff'],
                'columns': [],
                'total_bank_holidays': 0
            }
            
            # Fill in data for each column
            for column in bank_holiday_columns:
                if column['key'] in data['bank_holiday_counts']:
                    count = data['bank_holiday_counts'][column['key']]['count']
                    staff_row['columns'].append(count)
                    staff_row['total_bank_holidays'] += count
                else:
                    staff_row['columns'].append(0)
            
            bank_holiday_staff_list.append(staff_row)
    
    # Sort by staff name
    bank_holiday_staff_list.sort(
        key=lambda x: (x['staff'].user.last_name or x['staff'].user.username, x['staff'].user.first_name or '')
    )
    
    # Build period selection options
    current_year = datetime.now().year
    year_range = range(current_year - 5, current_year + 2)
    
    context = {
        'period_type': period_type,
        'year': year,
        'quarter': quarter,
        'month': month,
        'period_label': period_label,
        'staff_statistics': staff_list,
        'trainee_staff': trainee_staff,
        'oncall_staff': oncall_staff,
        'senior_staff': senior_staff,
        'overall_stats': overall_stats,
        'day_type_stats': dict(day_type_stats),
        'shift_type_stats': dict(shift_type_stats),
        'seniority_stats': dict(seniority_stats),
        'bank_holiday_staff': bank_holiday_staff_list,
        'bank_holiday_columns': bank_holiday_columns,
        'year_range': year_range,
        'months': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'quarters': [(i, f'Q{i}') for i in range(1, 5)],
    }
    
    return render(request, 'records/rota_statistics.html', context)