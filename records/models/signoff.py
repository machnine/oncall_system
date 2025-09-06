"""Sign-off models for monthly records and reports"""

from calendar import month_name

from django.db import models
from django.utils import timezone

from .staff import OnCallStaff


class MonthlySignOff(models.Model):
    """Monthly sign-off records to lock editing of time blocks and entries"""

    staff = models.ForeignKey(
        OnCallStaff, on_delete=models.CASCADE, related_name="monthly_signoffs"
    )
    year = models.IntegerField()
    month = models.IntegerField()  # 1-12
    signed_off_by = models.ForeignKey(
        OnCallStaff, on_delete=models.CASCADE, related_name="signoffs_given"
    )
    signed_off_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, help_text="Optional notes about this sign-off")

    class Meta:
        unique_together = ["staff", "year", "month"]
        verbose_name = "Monthly Sign-Off"
        verbose_name_plural = "Monthly Sign-Offs"
        ordering = ["-year", "-month", "staff__assignment_id"]

    def __str__(self):
        return f"{self.staff.assignment_id} - {self.year}/{self.month:02d} signed off by {self.signed_off_by.assignment_id}"

    @property
    def month_name(self):
        """Return the name of the month"""
        return month_name[self.month]

    @classmethod
    def is_month_signed_off(cls, staff, year, month):
        """Check if a specific month is signed off for a staff member"""
        return cls.objects.filter(staff=staff, year=year, month=month).exists()

    @classmethod
    def get_signoff_for_month(cls, staff, year, month):
        """Get the sign-off record for a specific month, or None if not signed off"""
        try:
            return cls.objects.get(staff=staff, year=year, month=month)
        except cls.DoesNotExist:
            return None


class MonthlyReportSignOff(models.Model):
    """Monthly report sign-off records to lock entire monthly reports for submission"""

    year = models.IntegerField()
    month = models.IntegerField()  # 1-12
    signed_off_by = models.ForeignKey(
        OnCallStaff, on_delete=models.CASCADE, related_name="report_signoffs_given"
    )
    signed_off_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, help_text="Notes about this report sign-off")
    total_staff_count = models.IntegerField(
        help_text="Number of staff included in this report"
    )
    total_hours = models.DecimalField(
        max_digits=8, decimal_places=2, help_text="Total hours for all staff"
    )
    total_claims = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Total claims for all staff"
    )

    class Meta:
        unique_together = ["year", "month"]
        verbose_name = "Monthly Report Sign-Off"
        verbose_name_plural = "Monthly Report Sign-Offs"
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"Monthly Report {self.year}/{self.month:02d} signed off by {self.signed_off_by.assignment_id}"

    @property
    def month_name(self):
        """Return the name of the month"""
        return month_name[self.month]

    @classmethod
    def is_report_signed_off(cls, year, month):
        """Check if a monthly report is signed off"""
        return cls.objects.filter(year=year, month=month).exists()

    @classmethod
    def get_report_signoff(cls, year, month):
        """Get the report sign-off record for a specific month, or None if not signed off"""
        try:
            return cls.objects.get(year=year, month=month)
        except cls.DoesNotExist:
            return None

    def get_staff_signoff_summary(self):
        """Get summary of individual staff sign-offs for this report month"""
        staff_signoffs = MonthlySignOff.objects.filter(year=self.year, month=self.month)
        total_staff = OnCallStaff.objects.count()
        signed_off_count = staff_signoffs.count()

        return {
            "signed_off_count": signed_off_count,
            "total_staff": total_staff,
            "pending_count": total_staff - signed_off_count,
            "all_signed_off": signed_off_count == total_staff,
            "staff_signoffs": staff_signoffs,
        }