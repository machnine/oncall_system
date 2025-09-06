"""Entity models (Donors, Recipients, Lab Tasks)"""

from django.db import models
from django.utils import timezone


class Donor(models.Model):
    """ Donor model """
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
    """ Recipient model """
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
    """
    Model representing a task other than donor or recipient assignments.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name