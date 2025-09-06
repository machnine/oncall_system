"""Admin configurations"""

from datetime import date

from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html

from .models import (
    Assignment,
    BankHoliday,
    DayType,
    Donor,
    LabTask,
    MonthlyReportSignOff,
    MonthlySignOff,
    OnCallStaff,
    Recipient,
    RotaEntry,
    RotaShift,
    TaskType,
    TimeBlock,
    TimeEntry,
    WorkMode,
)


@admin.register(OnCallStaff)
class OnCallStaffAdmin(admin.ModelAdmin):
    """
    Admin interface for On-call Staff model.
    """

    list_display = (
        "assignment_id",
        "get_full_name",
        "get_username",
        "seniority_level",
        "color_preview",
    )
    search_fields = (
        "assignment_id",
        "user__username",
        "user__first_name",
        "user__last_name",
    )
    list_filter = ("seniority_level",)
    fields = ("assignment_id", "user", "color", "seniority_level")

    @admin.display(description="Full Name")
    def get_full_name(self, obj):
        return obj.user.get_full_name()

    @admin.display(description="Username")
    def get_username(self, obj):
        return obj.user.username

    @admin.display(description="Color")
    def color_preview(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; display: inline-block; margin-right: 5px;"></div>{}',
            obj.color,
            obj.color,
        )


@admin.register(WorkMode)
class WorkModeAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
    search_fields = ("name",)


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
    search_fields = ("name",)


@admin.register(DayType)
class DayTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
    search_fields = ("name",)


@admin.register(LabTask)
class LabTaskAdmin(admin.ModelAdmin):
    list_display = ("name", "created")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ("donor_id", "name", "created")
    search_fields = ("donor_id", "name")
    list_filter = ("created",)
    ordering = ("donor_id",)


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ("recipient_id", "name", "created")
    search_fields = ("recipient_id", "name")
    list_filter = ("created",)
    ordering = ("recipient_id",)


class TimeEntryInline(admin.TabularInline):
    model = TimeEntry
    extra = 0
    fields = ("time_started", "time_ended", "task", "work_mode", "details", "get_hours")
    readonly_fields = ("get_hours",)

    @admin.display(description="Hours")
    def get_hours(self, obj):
        return obj.hours if obj.hours else 0


class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 0
    fields = ("entity_type", "entity_id", "notes")
    verbose_name = "Assignment"
    verbose_name_plural = "Assignments"


@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):
    list_display = (
        "staff",
        "formatted_date",
        "day_type",
        "get_total_hours",
        "get_block_claim",
    )
    list_filter = ("day_type", "date", "staff")
    search_fields = ("staff__assignment_id", "staff__user__username")
    date_hierarchy = "date"
    inlines = [AssignmentInline, TimeEntryInline]

    def formatted_date(self, obj):
        """Return date in yyyy-mm-dd format"""
        return obj.date.strftime("%Y-%m-%d")

    formatted_date.short_description = "Date"
    formatted_date.admin_order_field = "date"

    @admin.display(description="Total Hours")
    def get_total_hours(self, obj):
        return sum(entry.hours for entry in obj.time_entries.all())

    @admin.display(description="Block Claim")
    def get_block_claim(self, obj):
        return obj.claim if obj.claim else "-"

    @admin.display(description="Assignments")
    def get_assignment_count(self, obj):
        return obj.assignments.count()


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "timeblock",
        "entity_type",
        "entity_id",
        "get_entity_name",
        "display_color",
        "display_icon",
        "created",
    )
    list_filter = ("entity_type", "color", "timeblock__date", "timeblock__staff")
    search_fields = ("entity_id", "timeblock__staff__assignment_id")
    date_hierarchy = "timeblock__date"
    fields = ("timeblock", "entity_type", "entity_id", "notes", "color", "icon")

    @admin.display(description="Entity Name")
    def get_entity_name(self, obj):
        entity = obj.get_entity_object()
        if entity and hasattr(entity, "name") and entity.name:
            return entity.name
        return "-"


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = (
        "timeblock",
        "time_started",
        "time_ended",
        "task",
        "work_mode",
        "get_hours",
    )
    list_filter = ("timeblock__day_type", "timeblock__date")
    search_fields = ("timeblock__staff__assignment_id", "task__name", "work_mode__name")
    date_hierarchy = "timeblock__date"
    readonly_fields = ("get_hours",)

    @admin.display(description="Hours")
    def get_hours(self, obj):
        return obj.hours


@admin.register(MonthlySignOff)
class MonthlySignOffAdmin(admin.ModelAdmin):
    list_display = (
        "staff",
        "year",
        "month",
        "signed_off_by",
        "signed_off_at",
        "get_records_count",
    )
    list_filter = ("year", "month")
    search_fields = (
        "staff__assignment_id",
        "staff__user__username",
        "signed_off_by__assignment_id",
    )
    date_hierarchy = "signed_off_at"
    ordering = ["-year", "-month", "staff__assignment_id"]

    fields = ("staff", "year", "month", "signed_off_by", "notes")
    readonly_fields = ("signed_off_at",)

    @admin.display(description="Records")
    def get_records_count(self, obj):
        """Show how many time blocks were signed off for this month"""
        count = TimeBlock.objects.filter(
            staff=obj.staff, date__year=obj.year, date__month=obj.month
        ).count()
        return f"{count} time blocks"

    def save_model(self, request, obj, form, change):
        # Auto-set the signed_off_by field to the current user's staff record
        if not change:  # Only for new records
            try:
                obj.signed_off_by = OnCallStaff.objects.get(user=request.user)
            except OnCallStaff.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)


class RotaShiftInline(admin.TabularInline):
    model = RotaShift
    extra = 0
    fields = ("staff", "seniority_level", "notes")
    autocomplete_fields = ["staff"]


@admin.register(RotaEntry)
class RotaEntryAdmin(admin.ModelAdmin):
    list_display = ("formatted_date", "shift_type", "day_type", "get_staff_list")
    list_filter = ("date", "shift_type", "shifts__seniority_level")
    search_fields = (
        "date",
        "shifts__staff__assignment_id",
        "shifts__staff__user__username",
    )
    date_hierarchy = "date"

    def formatted_date(self, obj):
        """Return date in yyyy-mm-dd format"""
        return obj.date.strftime("%Y-%m-%d")

    formatted_date.short_description = "Date"
    formatted_date.admin_order_field = "date"
    ordering = ["-date"]
    inlines = [RotaShiftInline]

    @admin.display(description="On call staff")
    def get_staff_list(self, obj):
        staff_list = []
        for shift in obj.shifts.all()[:3]:  # Show first 3 staff
            shift_info = (
                f"{shift.staff.assignment_id} ({shift.get_seniority_level_display()})"
            )
            staff_list.append(shift_info)

        if obj.shifts.count() > 3:
            staff_list.append(f"... +{obj.shifts.count() - 3} more")

        return " - ".join(staff_list) if staff_list else "No staff assigned"


@admin.register(RotaShift)
class RotaShiftAdmin(admin.ModelAdmin):
    list_display = (
        "rota_entry",
        "staff",
        "seniority_level",
        "get_shift_type",
        "get_day_type",
        "created",
    )
    list_filter = (
        "seniority_level",
        "rota_entry__shift_type",
        "rota_entry__date",
        "created",
    )
    search_fields = (
        "staff__assignment_id",
        "staff__user__username",
        "rota_entry__date",
    )
    date_hierarchy = "rota_entry__date"
    ordering = ["-rota_entry__date", "seniority_level", "staff__assignment_id"]
    autocomplete_fields = ["staff"]

    @admin.display(description="Shift Type")
    def get_shift_type(self, obj):
        return obj.rota_entry.get_shift_type_display()

    @admin.display(description="Day Type")
    def get_day_type(self, obj):
        return obj.rota_entry.day_type


@admin.register(MonthlyReportSignOff)
class MonthlyReportSignOffAdmin(admin.ModelAdmin):
    """
    Admin interface for Monthly Report Sign Off model.
    """

    list_display = (
        "year",
        "month",
        "signed_off_by",
        "signed_off_at",
        "total_hours",
        "total_claims",
    )
    list_filter = ("year", "month", "signed_off_by", "signed_off_at")
    search_fields = ("signed_off_by__assignment_id",)
    date_hierarchy = "signed_off_at"
    ordering = ["-year", "-month"]


@admin.register(BankHoliday)
class BankHolidayAdmin(admin.ModelAdmin):
    """Admin interface for Bank Holidays with sync functionality"""

    list_display = ("formatted_date", "title", "notes")
    search_fields = ("title", "notes")
    date_hierarchy = "date"
    ordering = ["-date"]

    def formatted_date(self, obj):
        """Return date in yyyy-mm-dd format"""
        return obj.date.strftime("%Y-%m-%d")

    formatted_date.short_description = "Date"
    formatted_date.admin_order_field = "date"

    actions = ["sync_from_cached_file", "sync_from_uk_gov_api", "sync_auto"]

    def sync_from_cached_file(self, request, queryset=None):
        """Admin action to sync bank holidays from cached local file"""
        result = BankHoliday.sync_bank_holidays(source="local")

        if result["success"]:
            message = (
                f"Successfully synced {result['total']} bank holidays from {result['source']}. "
            )
            message += f"Created: {result['created']}, Updated: {result['updated']}"
            messages.success(request, message)
        else:
            messages.error(request, f"Failed to sync bank holidays: {result['error']}")

    sync_from_cached_file.short_description = "Sync bank holidays from cached file (2012-2027)"

    def sync_from_uk_gov_api(self, request, queryset=None):
        """Admin action to sync bank holidays from UK Gov API"""
        result = BankHoliday.sync_bank_holidays(source="api")

        if result["success"]:
            message = (
                f"Successfully synced {result['total']} bank holidays from {result['source']}. "
            )
            message += f"Created: {result['created']}, Updated: {result['updated']}"
            messages.success(request, message)
        else:
            messages.error(request, f"Failed to sync bank holidays: {result['error']}")

    sync_from_uk_gov_api.short_description = "Sync bank holidays from UK Government API (latest 3 years)"

    def sync_auto(self, request, queryset=None):
        """Admin action to sync bank holidays (cached file first, then API as fallback)"""
        result = BankHoliday.sync_bank_holidays(source="auto")

        if result["success"]:
            message = (
                f"Successfully synced {result['total']} bank holidays from {result['source']}. "
            )
            message += f"Created: {result['created']}, Updated: {result['updated']}"
            messages.success(request, message)
        else:
            messages.error(request, f"Failed to sync bank holidays: {result['error']}")

    sync_auto.short_description = "Sync bank holidays (auto: cached file first, then API fallback)"

    def changelist_view(self, request, extra_context=None):
        """Add custom context to the changelist view"""
        extra_context = extra_context or {}

        # Add some stats about the bank holidays
        current_year = date.today().year

        total_holidays = BankHoliday.objects.count()
        current_year_holidays = BankHoliday.objects.filter(
            date__year=current_year
        ).count()
        future_holidays = BankHoliday.objects.filter(date__gt=date.today()).count()

        extra_context["bank_holiday_stats"] = {
            "total": total_holidays,
            "current_year": current_year_holidays,
            "future": future_holidays,
        }

        return super().changelist_view(request, extra_context=extra_context)
