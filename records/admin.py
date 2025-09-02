from django.contrib import admin
from .models import OnCallStaff, WorkMode, Task, Detail, Block, TimeEntry


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
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


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


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('staff', 'date', 'day_type', 'get_total_hours', 'get_block_claim')
    list_filter = ('day_type', 'date', 'staff')
    search_fields = ('staff__assignment_id', 'staff__user__username')
    date_hierarchy = 'date'
    inlines = [TimeEntryInline]
    
    def get_total_hours(self, obj):
        return sum(entry.hours for entry in obj.time_entries.all())
    get_total_hours.short_description = 'Total Hours'
    
    def get_block_claim(self, obj):
        return obj.claim if obj.claim else '-'
    get_block_claim.short_description = 'Block Claim'


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('block', 'time_started', 'time_ended', 'task', 'work_mode', 'get_hours')
    list_filter = ('work_mode', 'task', 'block__day_type', 'block__date')
    search_fields = ('block__staff__assignment_id', 'task__name', 'work_mode__name')
    date_hierarchy = 'block__date'
    readonly_fields = ('get_hours',)
    
    def get_hours(self, obj):
        return obj.hours
    get_hours.short_description = 'Hours'
