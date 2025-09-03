from django.contrib import admin
from .models import OnCallStaff, WorkMode, TaskType, DayType, Detail, TimeBlock, TimeEntry, Donor, Recipient, LabTask, Assignment


@admin.register(OnCallStaff)
class OnCallStaffAdmin(admin.ModelAdmin):
    list_display = ('assignment_id', 'get_full_name', 'get_username')
    search_fields = ('assignment_id', 'user__username', 'user__first_name', 'user__last_name')
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'


@admin.register(WorkMode)
class WorkModeAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)
    list_filter = ('color',)


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
    search_fields = ("name",)
    list_display = ('name', 'color')
    search_fields = ('name',)
    list_filter = ('color',)


@admin.register(DayType)
class DayTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)
    list_filter = ('color',)


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('donor_id', 'name', 'created')
    search_fields = ('donor_id', 'name')
    list_filter = ('created',)
    ordering = ('donor_id',)


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ('recipient_id', 'name', 'created')
    search_fields = ('recipient_id', 'name')
    list_filter = ('created',)
    ordering = ('recipient_id',)


@admin.register(LabTask)
class LabTaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'created')
    search_fields = ('name', 'description')
    list_filter = ('created',)
    ordering = ('name',)


@admin.register(Detail)
class DetailAdmin(admin.ModelAdmin):
    list_display = ('get_short_text',)
    search_fields = ('text',)
    
    def get_short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    get_short_text.short_description = 'Detail Text'


class TimeEntryInline(admin.TabularInline):
    model = TimeEntry
    extra = 0
    fields = ('time_started', 'time_ended', 'task', 'work_mode', 'detail', 'get_hours')
    readonly_fields = ('get_hours',)
    
    def get_hours(self, obj):
        return obj.hours if obj.hours else 0
    get_hours.short_description = 'Hours'


class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 0
    fields = ('entity_type', 'entity_id', 'notes')
    verbose_name = "Assignment"
    verbose_name_plural = "Assignments"


@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):
    list_display = ('staff', 'date', 'day_type', 'get_total_hours', 'get_block_claim', 'get_assignment_count')
    list_filter = ('day_type', 'date', 'staff')
    search_fields = ('staff__assignment_id', 'staff__user__username')
    date_hierarchy = 'date'
    inlines = [AssignmentInline, TimeEntryInline]
    
    def get_total_hours(self, obj):
        return sum(entry.hours for entry in obj.time_entries.all())
    get_total_hours.short_description = 'Total Hours'
    
    def get_block_claim(self, obj):
        return obj.claim if obj.claim else '-'
    get_block_claim.short_description = 'Block Claim'
    
    def get_assignment_count(self, obj):
        return obj.assignments.count()
    get_assignment_count.short_description = 'Assignments'


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('timeblock', 'entity_type', 'entity_id', 'get_entity_name', 'display_color', 'display_icon', 'created')
    list_filter = ('entity_type', 'color', 'timeblock__date', 'timeblock__staff')
    search_fields = ('entity_id', 'timeblock__staff__assignment_id')
    date_hierarchy = 'timeblock__date'
    fields = ('timeblock', 'entity_type', 'entity_id', 'notes', 'color', 'icon')

    def get_entity_name(self, obj):
        entity = obj.get_entity_object()
        if entity and hasattr(entity, 'name') and entity.name:
            return entity.name
        return '-'
    get_entity_name.short_description = 'Entity Name'


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('timeblock', 'time_started', 'time_ended', 'task', 'work_mode', 'get_hours')
    list_filter = ('work_mode', 'task', 'timeblock__day_type', 'timeblock__date')
    search_fields = ('timeblock__staff__assignment_id', 'task__name', 'work_mode__name')
    date_hierarchy = 'timeblock__date'
    readonly_fields = ('get_hours',)
    
    def get_hours(self, obj):
        return obj.hours
    get_hours.short_description = 'Hours'
