"""TimeBlock management views"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import TimeBlockEditForm, TimeBlockForm
from ..models import TimeBlock
from ..utils.decorators import (
    check_month_not_signed_off,
    check_timeblock_not_signed_off,
    require_oncall_staff,
)
from .dashboard_views import get_dashboard_url_with_date


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