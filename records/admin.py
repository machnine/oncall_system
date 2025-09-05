from django.contrib import admin
from django.utils.html import format_html
from .models import (
    OnCallStaff,
    WorkMode,
    TaskType,
    DayType,
    Detail,
    TimeBlock,
    TimeEntry,
    Donor,
    Recipient,
    LabTask,
    Assignment,
    MonthlySignOff,
    MonthlyReportSignOff,
    RotaEntry,
    RotaShift,
)


@admin.register(OnCallStaff)
class OnCallStaffAdmin(admin.ModelAdmin):
    list_display = ("assignment_id", "get_full_name", "get_username", "seniority_level", "color_preview")
    search_fields = (
        "assignment_id",
        "user__username",
        "user__first_name",
        "user__last_name",
    )
    list_filter = ("seniority_level",)
    fields = ("assignment_id", "user", "color", "seniority_level")

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    get_full_name.short_description = "Full Name"

    def get_username(self, obj):
        return obj.user.username

    get_username.short_description = "Username"

    def color_preview(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; display: inline-block; margin-right: 5px;"></div>{}',
            obj.color,
            obj.color)

    color_preview.short_description = "Color"


@admin.register(WorkMode)
class WorkModeAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
    search_fields = ("name",)
    list_filter = ("color",)


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
    search_fields = ("name",)
    list_display = ("name", "color")
    search_fields = ("name",)
    list_filter = ("color",)


@admin.register(DayType)
class DayTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
    search_fields = ("name",)
    list_filter = ("color",)


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


@admin.register(LabTask)
class LabTaskAdmin(admin.ModelAdmin):
    list_display = ("name", "created")
    search_fields = ("name", "description")
    list_filter = ("created",)
    ordering = ("name",)


@admin.register(Detail)
class DetailAdmin(admin.ModelAdmin):
    list_display = ("get_short_text",)
    search_fields = ("text",)

    def get_short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    get_short_text.short_description = "Detail Text"


class TimeEntryInline(admin.TabularInline):
    model = TimeEntry
    extra = 0
    fields = ("time_started", "time_ended", "task", "work_mode", "detail", "get_hours")
    readonly_fields = ("get_hours",)

    def get_hours(self, obj):
        return obj.hours if obj.hours else 0

    get_hours.short_description = "Hours"


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
        "date",
        "day_type",
        "get_total_hours",
        "get_block_claim",
        "get_assignment_count",
    )
    list_filter = ("day_type", "date", "staff")
    search_fields = ("staff__assignment_id", "staff__user__username")
    date_hierarchy = "date"
    inlines = [AssignmentInline, TimeEntryInline]

    def get_total_hours(self, obj):
        return sum(entry.hours for entry in obj.time_entries.all())

    get_total_hours.short_description = "Total Hours"

    def get_block_claim(self, obj):
        return obj.claim if obj.claim else "-"

    get_block_claim.short_description = "Block Claim"

    def get_assignment_count(self, obj):
        return obj.assignments.count()

    get_assignment_count.short_description = "Assignments"


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

    def get_entity_name(self, obj):
        entity = obj.get_entity_object()
        if entity and hasattr(entity, "name") and entity.name:
            return entity.name
        return "-"

    get_entity_name.short_description = "Entity Name"


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
    list_filter = ("work_mode", "task", "timeblock__day_type", "timeblock__date")
    search_fields = ("timeblock__staff__assignment_id", "task__name", "work_mode__name")
    date_hierarchy = "timeblock__date"
    readonly_fields = ("get_hours",)

    def get_hours(self, obj):
        return obj.hours

    get_hours.short_description = "Hours"


@admin.register(MonthlySignOff)
class MonthlySignOffAdmin(admin.ModelAdmin):
    list_display = (
        "staff",
        "year",
        "month",
        "month_name",
        "signed_off_by",
        "signed_off_at",
        "get_records_count",
    )
    list_filter = ("year", "month", "signed_off_by", "signed_off_at")
    search_fields = (
        "staff__assignment_id",
        "staff__user__username",
        "signed_off_by__assignment_id",
    )
    date_hierarchy = "signed_off_at"
    ordering = ["-year", "-month", "staff__assignment_id"]

    fields = ("staff", "year", "month", "signed_off_by", "notes")
    readonly_fields = ("signed_off_at",)

    def get_records_count(self, obj):
        """Show how many time blocks were signed off for this month"""
        from .models import TimeBlock

        count = TimeBlock.objects.filter(
            staff=obj.staff, date__year=obj.year, date__month=obj.month
        ).count()
        return f"{count} time blocks"

    get_records_count.short_description = "Records"

    def save_model(self, request, obj, form, change):
        # Auto-set the signed_off_by field to the current user's staff record
        if not change:  # Only for new records
            try:
                from .models import OnCallStaff

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
    list_display = (
        "date",
        "shift_type",
        "day_type",
        "get_shift_count",
        "get_staff_list",
        "is_bank_holiday",
    )
    list_filter = ("date", "shift_type", "shifts__seniority_level")
    search_fields = (
        "date",
        "shifts__staff__assignment_id",
        "shifts__staff__user__username",
    )
    date_hierarchy = "date"
    ordering = ["-date"]
    inlines = [RotaShiftInline]

    def get_shift_count(self, obj):
        return obj.shifts.count()

    get_shift_count.short_description = "Total Shifts"

    def get_staff_list(self, obj):
        staff_list = []
        for shift in obj.shifts.all()[:3]:  # Show first 3 staff
            shift_info = (
                f"{shift.staff.assignment_id} ({shift.get_seniority_level_display()})"
            )
            staff_list.append(shift_info)

        if obj.shifts.count() > 3:
            staff_list.append(f"... +{obj.shifts.count() - 3} more")

        return ", ".join(staff_list) if staff_list else "No staff assigned"

    get_staff_list.short_description = "Staff Assigned"


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

    def get_shift_type(self, obj):
        return obj.rota_entry.get_shift_type_display()

    get_shift_type.short_description = "Shift Type"

    def get_day_type(self, obj):
        return obj.rota_entry.day_type

    get_day_type.short_description = "Day Type"


@admin.register(MonthlyReportSignOff)
class MonthlyReportSignOffAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "month",
        "month_name",
        "signed_off_by",
        "signed_off_at",
        "total_staff_count",
        "total_hours",
        "total_claims",
    )
    list_filter = ("year", "month", "signed_off_by", "signed_off_at")
    search_fields = ("signed_off_by__assignment_id",)
    date_hierarchy = "signed_off_at"
    ordering = ["-year", "-month"]

    fields = (
        "year",
        "month",
        "signed_off_by",
        "notes",
        "total_staff_count",
        "total_hours",
        "total_claims",
    )
    readonly_fields = ("signed_off_at",)

    def save_model(self, request, obj, form, change):
        # Auto-set the signed_off_by field to the current user's staff record
        if not change:  # Only for new records
            try:
                from .models import OnCallStaff

                obj.signed_off_by = OnCallStaff.objects.get(user=request.user)
            except OnCallStaff.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)
