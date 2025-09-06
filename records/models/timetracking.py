"""Time tracking models (TimeBlock, TimeEntry, Assignment)"""

from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .config import DayType, TaskType, WorkMode
from .constants import ASSIGNMENT_TYPE_CONFIG
from .entities import Donor, LabTask, Recipient
from .staff import OnCallStaff


class TimeBlock(models.Model):
    """
    Model representing a block of time recorded for actual on-call activities.
    """

    ONCALL_TYPE_CHOICES = [("normal", "Normal"), ("nhsp", "NHSP")]

    staff = models.ForeignKey(OnCallStaff, on_delete=models.CASCADE)
    date = models.DateField()
    day_type = models.ForeignKey(
        DayType, on_delete=models.CASCADE, null=True, blank=True
    )
    oncall_type = models.CharField(
        max_length=20, choices=ONCALL_TYPE_CHOICES, default="normal"
    )
    claim = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(auto_now=True)

    def clean(self):
        # Prevent future dates
        if self.date and self.date > timezone.now().date():
            raise ValidationError("Block date cannot be in the future.")

    def save(self, *args, **kwargs):
        if not self.day_type:
            # Auto-determine day type if not set
            if self.date.weekday() == 5:  # Saturday
                self.day_type = DayType.objects.get_or_create(
                    name="Saturday", defaults={"color": "warning"}
                )[0]
            elif self.date.weekday() == 6:  # Sunday
                self.day_type = DayType.objects.get_or_create(
                    name="Sunday", defaults={"color": "danger"}
                )[0]
            else:
                self.day_type = DayType.objects.get_or_create(
                    name="Weekday", defaults={"color": "success"}
                )[0]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.staff.assignment_id} - {self.date} ({self.day_type})"


class Assignment(models.Model):
    """Links TimeBlock to entities"""

    ENTITY_TYPES = [
        ("donor", "Donor"),
        ("recipient", "Recipient"),
        ("lab_task", "Lab Task"),
    ]

    timeblock = models.ForeignKey(
        TimeBlock, on_delete=models.CASCADE, related_name="assignments"
    )
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    entity_id = models.CharField(max_length=50, help_text="ID of the assigned entity")
    notes = models.TextField(blank=True)
    color = models.CharField(
        max_length=20,
        default="primary",
        help_text="Bootstrap color for the assignment badge",
    )
    icon = models.CharField(
        max_length=50, default="bi-person-fill", help_text="Bootstrap icon class"
    )
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ["timeblock", "entity_type", "entity_id"]
        verbose_name = "Assignment"
        verbose_name_plural = "Assignments"

    def get_entity_object(self):
        """Get the actual entity object based on type and ID"""
        try:
            if self.entity_type == "donor":
                return Donor.objects.get(donor_id=self.entity_id)
            elif self.entity_type == "recipient":
                return Recipient.objects.get(recipient_id=self.entity_id)
            elif self.entity_type == "lab_task":
                return LabTask.objects.get(name=self.entity_id)
        except (Donor.DoesNotExist, Recipient.DoesNotExist, LabTask.DoesNotExist):
            return None
        return None

    def get_assignment_type_config(self):
        """Get the configuration for this assignment type"""
        return ASSIGNMENT_TYPE_CONFIG.get(self.entity_type, {})

    @property
    def display_color(self):
        """Get color from config or use direct field as fallback"""
        config = self.get_assignment_type_config()
        return config.get("color", self.color)

    @property
    def display_icon(self):
        """Get icon from config or use direct field as fallback"""
        config = self.get_assignment_type_config()
        return config.get("icon", self.icon)

    def __str__(self):
        entity_obj = self.get_entity_object()
        if entity_obj:
            return f"{self.timeblock} assigned to {entity_obj}"
        return f"{self.timeblock} assigned to {self.entity_type}: {self.entity_id}"


class TimeEntry(models.Model):
    """
    Represents a single time entry for a staff member during an on-call time block
    """

    timeblock = models.ForeignKey(
        TimeBlock, on_delete=models.CASCADE, related_name="time_entries"
    )
    time_started = models.TimeField()
    time_ended = models.TimeField()
    task = models.ForeignKey(TaskType, on_delete=models.CASCADE)
    details = models.TextField(
        blank=True, help_text="Optional details about this time entry"
    )
    work_mode = models.ForeignKey(WorkMode, on_delete=models.CASCADE)
    created = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(auto_now=True)

    @property
    def hours(self):
        """Calculate hours worked, handling overnight blocks (17:30-08:30+1)"""
        start = datetime.combine(self.timeblock.date, self.time_started)
        end = datetime.combine(self.timeblock.date, self.time_ended)

        # If end time is before start time, it's the next day
        if self.time_ended <= self.time_started:
            end += timedelta(days=1)

        duration = end - start
        return round(duration.total_seconds() / 3600, 2)

    def clean(self):
        # Basic validation - end time should be different from start time
        if self.time_started == self.time_ended:
            raise ValidationError("Start time and end time cannot be the same.")

    def __str__(self):
        return f"{self.timeblock.staff.assignment_id} - {self.timeblock.date} - {self.task.name} ({self.hours}h)"