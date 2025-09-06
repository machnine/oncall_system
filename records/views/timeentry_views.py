"""TimeEntry management views"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import TimeEntryForm
from ..models import TimeBlock, TimeEntry
from ..utils.decorators import check_month_not_signed_off, require_oncall_staff
from .dashboard_views import get_dashboard_url_with_date


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