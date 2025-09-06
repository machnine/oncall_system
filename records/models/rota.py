"""Rota scheduling models"""

from django.db import models
from django.utils import timezone

from .holidays import BankHoliday
from .staff import OnCallStaff


class RotaEntry(models.Model):
    """Represents a single day's on-call rota"""

    SHIFT_TYPE_CHOICES = [("normal", "Normal"), ("nhsp", "NHSP")]

    date = models.DateField()
    shift_type = models.CharField(
        max_length=10, choices=SHIFT_TYPE_CHOICES, default="normal"
    )
    created = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rota Date"
        verbose_name_plural = "Rota Dates"
        ordering = ["date"]
        unique_together = ["date"]

    def __str__(self):
        return f"Rota for {self.date.strftime('%Y-%m-%d')}"

    @property
    def is_bank_holiday(self):
        """Check if this date is a bank holiday"""
        return BankHoliday.is_bank_holiday(self.date)

    @property
    def day_type(self):
        """Get the day type (Weekday/Saturday/Sunday/BankHoliday)"""
        if self.is_bank_holiday:
            return "BankHoliday"
        elif self.date.weekday() == 5:  # Saturday
            return "Saturday"
        elif self.date.weekday() == 6:  # Sunday
            return "Sunday"
        else:
            return "Weekday"

    def get_shifts_by_type(self):
        """Get shifts grouped by shift type (all shifts on a day have the same type)"""
        shifts = list(self.shifts.all().select_related("staff"))

        if self.shift_type == "nhsp":
            return {"normal": [], "nhsp": shifts}
        else:
            return {"normal": shifts, "nhsp": []}


class RotaShift(models.Model):
    """Individual shift assignment within a rota entry"""

    SENIORITY_CHOICES = [
        ("trainee", "Trainee"),
        ("oncall", "On-Call"),
        ("senior", "Senior"),
    ]

    rota_entry = models.ForeignKey(
        RotaEntry, on_delete=models.CASCADE, related_name="shifts"
    )
    staff = models.ForeignKey(OnCallStaff, on_delete=models.CASCADE)
    seniority_level = models.CharField(max_length=10, choices=SENIORITY_CHOICES)
    notes = models.TextField(blank=True, help_text="Optional notes for this shift")
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Rota Staff"
        verbose_name_plural = "Rota Staff"
        ordering = ["seniority_level", "staff__assignment_id"]
        unique_together = ["rota_entry", "staff"]

    def __str__(self):
        return f"{self.staff.assignment_id} - {self.rota_entry.date} ({self.get_seniority_level_display()})"