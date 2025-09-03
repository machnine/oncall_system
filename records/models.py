from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class OnCallStaff(models.Model):
    assignment_id = models.CharField(max_length=50, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.assignment_id} - {self.user.get_full_name()}"


class WorkMode(models.Model):
    BOOTSTRAP_COLORS = [
        ("primary", "Primary (Blue)"),
        ("secondary", "Secondary (Gray)"),
        ("success", "Success (Green)"),
        ("danger", "Danger (Red)"),
        ("warning", "Warning (Yellow)"),
        ("info", "Info (Cyan)"),
        ("light", "Light"),
        ("dark", "Dark"),
    ]

    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=20, choices=BOOTSTRAP_COLORS, default="primary")

    def __str__(self):
        return self.name


class TaskType(models.Model):
    BOOTSTRAP_COLORS = [
        ("primary", "Primary (Blue)"),
        ("secondary", "Secondary (Gray)"),
        ("success", "Success (Green)"),
        ("danger", "Danger (Red)"),
        ("warning", "Warning (Yellow)"),
        ("info", "Info (Cyan)"),
        ("light", "Light"),
        ("dark", "Dark"),
    ]

    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(
        max_length=20, choices=BOOTSTRAP_COLORS, default="secondary"
    )

    def __str__(self):
        return self.name


class DayType(models.Model):
    BOOTSTRAP_COLORS = [
        ("primary", "Primary (Blue)"),
        ("secondary", "Secondary (Gray)"),
        ("success", "Success (Green)"),
        ("danger", "Danger (Red)"),
        ("warning", "Warning (Yellow)"),
        ("info", "Info (Cyan)"),
        ("light", "Light"),
        ("dark", "Dark"),
    ]

    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=20, choices=BOOTSTRAP_COLORS, default="info")

    def __str__(self):
        return self.name


class Detail(models.Model):
    text = models.TextField()

    def __str__(self):
        return self.text[:50] + "..." if len(self.text) > 50 else self.text


class TimeBlock(models.Model):
    staff = models.ForeignKey(OnCallStaff, on_delete=models.CASCADE)
    date = models.DateField()
    day_type = models.ForeignKey(
        DayType, on_delete=models.CASCADE, null=True, blank=True
    )
    claim = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total claim hours for this block",
    )
    created = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        # Removed unique_together to allow multiple blocks per day
        pass

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils import timezone

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


class Donor(models.Model):
    donor_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Donor identifier (can be numeric or text)",
    )
    name = models.CharField(max_length=100, blank=True, help_text="Optional donor name")
    notes = models.TextField(blank=True, help_text="Additional notes about this donor")
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Donor {self.donor_id}" + (f" ({self.name})" if self.name else "")


class Recipient(models.Model):
    recipient_id = models.CharField(
        max_length=50, unique=True, help_text="Unique recipient identifier"
    )
    name = models.CharField(
        max_length=100, blank=True, help_text="Optional recipient name"
    )
    notes = models.TextField(
        blank=True, help_text="Additional notes about this recipient"
    )
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Recipient {self.recipient_id}" + (
            f" ({self.name})" if self.name else ""
        )


class LabTask(models.Model):
    name = models.CharField(
        max_length=100, unique=True, help_text="Lab task name/description"
    )
    description = models.TextField(
        blank=True, help_text="Detailed description of the lab task"
    )
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


# Assignment Type Configuration - This can be moved to a database table later if needed
ASSIGNMENT_TYPE_CONFIG = {
    "donor": {
        "name": "Donor",
        "color": "success",
        "icon": "bi-person-check",
        "description": "Blood/organ donor assignments",
    },
    "recipient": {
        "name": "Recipient",
        "color": "info",
        "icon": "bi-person-fill",
        "description": "Blood/organ recipient assignments",
    },
    "lab_task": {
        "name": "Lab Task",
        "color": "warning",
        "icon": "bi-thermometer-low",
        "description": "Laboratory task assignments",
    },
}


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
    notes = models.TextField(
        blank=True, help_text="Notes about this assignment during this time block"
    )
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
    timeblock = models.ForeignKey(
        TimeBlock, on_delete=models.CASCADE, related_name="time_entries"
    )
    time_started = models.TimeField()
    time_ended = models.TimeField()
    task = models.ForeignKey(TaskType, on_delete=models.CASCADE)
    detail = models.ForeignKey(Detail, on_delete=models.SET_NULL, null=True, blank=True)
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
        from django.core.exceptions import ValidationError

        # Basic validation - end time should be different from start time
        if self.time_started == self.time_ended:
            raise ValidationError("Start time and end time cannot be the same.")

    def __str__(self):
        return f"{self.timeblock.staff.assignment_id} - {self.timeblock.date} - {self.task.name} ({self.hours}h)"
