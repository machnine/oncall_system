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
    def sync_bank_holidays(cls, source="auto", region="england-and-wales"):
        """
        Sync bank holidays from either cached file or UK Government API
        
        Args:
            source: "auto" (try cached file first, then API), "local", or "api"
            region: "england-and-wales", "scotland", or "northern-ireland"
        """
        import json
        import os
        import requests
        from datetime import datetime
        from django.conf import settings

        def process_holidays_data(data, data_source):
            """Process holidays data from either source"""
            if not data or region not in data:
                return {"success": False, "error": f"No data found for region: {region}"}
            
            england_wales_holidays = data.get(region, {}).get("events", [])
            
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
                "source": data_source,
            }

        # Try cached file first if source is auto or local
        if source in ["auto", "local"]:
            try:
                cached_file_path = os.path.join(settings.BASE_DIR, "static", "data", "bank-holidays-2012-2027.json")
                
                if os.path.exists(cached_file_path):
                    with open(cached_file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                    
                    result = process_holidays_data(data, "local cached file")
                    if result["success"]:
                        return result
                elif source == "local":
                    return {"success": False, "error": "Cached file not found"}
            except Exception as e:
                if source == "local":
                    return {"success": False, "error": f"Local file error: {str(e)}"}
                # Continue to API if source is auto

        # Try UK Government API if source is auto or api
        if source in ["auto", "api"]:
            try:
                response = requests.get("https://www.gov.uk/bank-holidays.json", timeout=30)
                response.raise_for_status()
                data = response.json()
                
                result = process_holidays_data(data, "UK Government API")
                return result

            except requests.RequestException as e:
                error_msg = f"API request failed: {str(e)}"
                if source == "api":
                    return {"success": False, "error": error_msg}
                else:
                    return {"success": False, "error": f"Both local file and API failed. API error: {error_msg}"}
            except Exception as e:
                return {"success": False, "error": f"Unexpected API error: {str(e)}"}

        return {"success": False, "error": f"Invalid source: {source}"}

    @classmethod
    def sync_from_uk_gov_api(cls):
        """Legacy method for backward compatibility - uses API only"""
        return cls.sync_bank_holidays(source="api")