"""Configuration models for the on-call system"""

from django.db import models
from .constants import BOOTSTRAP_COLORS


class WorkMode(models.Model):
    """WFH / Lab / Senior cover etc."""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=20, choices=BOOTSTRAP_COLORS, default="primary")

    def __str__(self):
        return self.name


class TaskType(models.Model):
    """Type of task performed during on-call time entry"""

    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(
        max_length=20, choices=BOOTSTRAP_COLORS, default="secondary"
    )

    def __str__(self):
        return self.name


class DayType(models.Model):
    """Day type for TimeBlock (e.g. Weekday, Saturday, Sunday)"""

    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=20, choices=BOOTSTRAP_COLORS, default="info")

    def __str__(self):
        return self.name