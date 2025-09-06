"""Staff-related models"""

from django.contrib.auth.models import User
from django.db import models


class OnCallStaff(models.Model):
    """
    Model representing an on-call staff member.
    """

    SENIORITY_CHOICES = [
        ("trainee", "Trainee"),
        ("oncall", "On-Call"),
        ("senior", "Senior"),
    ]

    assignment_id = models.CharField(max_length=50, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    color = models.CharField(
        max_length=7,
        default="#6c757d",
        help_text="Hex color code for this staff member (e.g. #ff5733)",
    )
    seniority_level = models.CharField(
        max_length=10,
        choices=SENIORITY_CHOICES,
        default="trainee",
        help_text="Seniority level of this staff member",
    )

    def __str__(self):
        return f"{self.assignment_id} - {self.user.get_full_name()} ({self.get_seniority_level_display()})"

    class Meta:
        verbose_name = "On-call Staff"
        verbose_name_plural = "On-call Staff"