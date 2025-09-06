"""Bank holiday models and management"""

from django.db import models


class BankHoliday(models.Model):
    """UK Bank Holidays storage"""

    date = models.DateField(unique=True, db_index=True)
    title = models.CharField(max_length=200, help_text="Name of the bank holiday")
    notes = models.TextField(blank=True, help_text="Additional notes")

    class Meta:
        ordering = ["date"]
        verbose_name = "Bank Holiday"
        verbose_name_plural = "Bank Holidays"

    def __str__(self):
        return f"{self.title} - {self.date}"

    @classmethod
    def is_bank_holiday(cls, date):
        """Check if a given date is a bank holiday"""
        return cls.objects.filter(date=date).exists()

    @classmethod
    def get_bank_holidays_in_range(cls, start_date, end_date):
        """Get all bank holidays within a date range"""
        return cls.objects.filter(date__gte=start_date, date__lte=end_date)

    @classmethod
    def sync_from_uk_gov_api(cls):
        """Fetch bank holidays from UK Government API and update database"""
        import requests
        from datetime import datetime

        try:
            response = requests.get("https://www.gov.uk/bank-holidays.json", timeout=30)
            response.raise_for_status()
            data = response.json()

            # UK Gov API returns data for different regions
            # We'll use England and Wales as default
            england_wales_holidays = data.get("england-and-wales", {}).get("events", [])

            created_count = 0
            updated_count = 0

            for holiday_data in england_wales_holidays:
                holiday_date = datetime.strptime(
                    holiday_data["date"], "%Y-%m-%d"
                ).date()

                holiday, created = cls.objects.update_or_create(
                    date=holiday_date,
                    defaults={
                        "title": holiday_data["title"],
                        "notes": holiday_data.get("notes", ""),
                    },
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            return {
                "success": True,
                "created": created_count,
                "updated": updated_count,
                "total": len(england_wales_holidays),
            }

        except requests.RequestException as e:
            return {"success": False, "error": f"API request failed: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}