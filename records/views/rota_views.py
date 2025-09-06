"""Rota management views for scheduling on-call staff"""

import calendar
import json
from datetime import date, datetime

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