from django import forms
from django.utils import timezone
from govuk_bank_holidays.bank_holidays import BankHolidays
from .models import (
    TimeBlock,
    TimeEntry,
    Detail,
    Donor,
    Recipient,
    LabTask,
    Assignment,
    DayType,
    TaskType,
    WorkMode,
    ASSIGNMENT_TYPE_CONFIG,
)


class TimeBlockForm(forms.ModelForm):
    # Assignment fields (for UI only - actual data comes from assignments_data)
    assignment_type = forms.ChoiceField(
        choices=[
            ("", "No assignment"),
            ("donor", "Donor"),
            ("recipient", "Recipient"),
            ("lab_task", "Lab Task"),
        ],
        initial="donor",
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "assignment_type"}),
    )
    entity_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "entity_id",
                "placeholder": "Enter ID or select from shortcuts",
            }
        ),
    )
    assignment_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Optional notes about this assignment",
            }
        ),
    )

    # Hidden field for assignments JSON data
    assignments_data = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date to today if this is a new form (no instance)
        if not self.instance.pk:
            self.fields["date"].initial = timezone.now().date()

        # Set max date to today for client-side validation
        today = timezone.now().date().isoformat()
        self.fields["date"].widget.attrs["max"] = today

        # Store recent entities for template access
        self.recent_donors = list(Donor.objects.order_by("-created")[:5])
        self.recent_recipients = list(Recipient.objects.order_by("-created")[:5])
        self.recent_lab_tasks = list(LabTask.objects.order_by("-created")[:5])

    def clean_date(self):
        date = self.cleaned_data.get("date")
        if date and date > timezone.now().date():
            raise forms.ValidationError("Block date cannot be in the future.")
        return date

    def get_day_type(self, date):
        """Automatically determine day type based on date using official UK government data"""
        if not date:
            return None

        # Get UK bank holidays from official government data
        bank_holidays = BankHolidays()
        uk_holidays = bank_holidays.get_holidays("england-and-wales", date.year)

        # Create a set of holiday dates for efficient lookup
        holiday_dates = {holiday["date"] for holiday in uk_holidays}

        # Determine the day type name
        if date in holiday_dates:
            day_type_name = "BankHoliday"
        elif date.weekday() < 5:  # Monday-Friday (0-4)
            day_type_name = "Weekday"
        elif date.weekday() == 5:  # Saturday
            day_type_name = "Saturday"
        else:  # Sunday
            day_type_name = "Sunday"

        # Get or create the DayType object
        try:
            day_type, created = DayType.objects.get_or_create(
                name=day_type_name,
                defaults={"color": self._get_default_color(day_type_name)},
            )
            return day_type
        except Exception:
            return None

    def _get_default_color(self, day_type_name):
        """Get default color for day type"""
        color_map = {
            "Weekday": "success",
            "Saturday": "warning",
            "Sunday": "danger",
            "BankHoliday": "info",
        }
        return color_map.get(day_type_name, "primary")

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get("date")

        # Auto-detect and set day type
        if date:
            cleaned_data["day_type"] = self.get_day_type(date)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set the auto-detected day type
        if hasattr(self, "cleaned_data") and "day_type" in self.cleaned_data:
            instance.day_type = self.cleaned_data["day_type"]

        if commit:
            instance.save()

            # Handle multiple assignments from JSON data
            assignments_data = self.cleaned_data.get("assignments_data", "")

            if assignments_data:
                import json

                try:
                    assignments = json.loads(assignments_data)

                    for assignment_data in assignments:
                        assignment_type = assignment_data.get("type")
                        entity_id = assignment_data.get("entity_id")
                        notes = assignment_data.get("notes", "")

                        if assignment_type and entity_id:
                            # Create or get the entity
                            entity = self._get_or_create_entity(
                                assignment_type, entity_id
                            )

                            if entity:
                                # Get default styling from AssignmentType if available
                                color, icon = self._get_default_styling(assignment_type)

                                # Create assignment
                                Assignment.objects.get_or_create(
                                    timeblock=instance,
                                    entity_type=assignment_type,
                                    entity_id=entity_id,
                                    defaults={
                                        "notes": notes,
                                        "color": color,
                                        "icon": icon,
                                    },
                                )
                except (json.JSONDecodeError, KeyError) as e:
                    # Log error but don't fail the form save
                    pass

        return instance

    def _get_or_create_entity(self, entity_type, entity_id):
        """Create or get entity based on type and ID"""
        try:
            if entity_type == "donor":
                entity, created = Donor.objects.get_or_create(donor_id=entity_id)
                return entity
            elif entity_type == "recipient":
                entity, created = Recipient.objects.get_or_create(
                    recipient_id=entity_id
                )
                return entity
            elif entity_type == "lab_task":
                entity, created = LabTask.objects.get_or_create(name=entity_id)
                return entity
        except Exception:
            pass
        return None

    def _get_default_styling(self, entity_type):
        """Get default color and icon from configuration"""
        config = ASSIGNMENT_TYPE_CONFIG.get(entity_type, {})
        return config.get("color", "primary"), config.get("icon", "bi-person-fill")

    class Meta:
        model = TimeBlock
        fields = ["date", "oncall_type"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "oncall_type": forms.RadioSelect(attrs={"class": "form-check-input"}),
        }


class TimeBlockEditForm(forms.ModelForm):
    """Form for editing existing blocks - includes claim field and assignments"""

    # Assignment fields (for UI only - actual data comes from assignments_data)
    assignment_type = forms.ChoiceField(
        choices=[
            ("", "No assignment"),
            ("donor", "Donor"),
            ("recipient", "Recipient"),
            ("lab_task", "Lab Task"),
        ],
        initial="donor",
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "assignment_type"}),
    )
    entity_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "entity_id",
                "placeholder": "Enter ID or select from shortcuts",
            }
        ),
    )
    assignment_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Optional notes about this assignment",
            }
        ),
    )

    # Hidden field for assignments JSON data
    assignments_data = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set max date to today for client-side validation
        today = timezone.now().date().isoformat()
        self.fields["date"].widget.attrs["max"] = today

        # Store recent entities for template access
        self.recent_donors = list(Donor.objects.order_by("-created")[:10])
        self.recent_recipients = list(Recipient.objects.order_by("-created")[:10])
        self.recent_lab_tasks = list(LabTask.objects.order_by("-created")[:10])

    def clean_date(self):
        date = self.cleaned_data.get("date")
        if date and date > timezone.now().date():
            raise forms.ValidationError("Block date cannot be in the future.")
        return date

    def get_day_type(self, date):
        """Automatically determine day type based on date using official UK government data"""
        if not date:
            return None

        # Get UK bank holidays from official government data
        bank_holidays = BankHolidays()
        uk_holidays = bank_holidays.get_holidays("england-and-wales", date.year)

        # Create a set of holiday dates for efficient lookup
        holiday_dates = {holiday["date"] for holiday in uk_holidays}

        # Determine the day type name
        if date in holiday_dates:
            day_type_name = "BankHoliday"
        elif date.weekday() < 5:  # Monday-Friday (0-4)
            day_type_name = "Weekday"
        elif date.weekday() == 5:  # Saturday
            day_type_name = "Saturday"
        else:  # Sunday
            day_type_name = "Sunday"

        # Get or create the DayType object
        try:
            day_type, created = DayType.objects.get_or_create(
                name=day_type_name,
                defaults={"color": self._get_default_color(day_type_name)},
            )
            return day_type
        except Exception:
            return None

    def _get_default_color(self, day_type_name):
        """Get default color for day type"""
        color_map = {
            "Weekday": "success",
            "Saturday": "warning",
            "Sunday": "danger",
            "BankHoliday": "info",
        }
        return color_map.get(day_type_name, "primary")

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get("date")

        # Auto-detect and set day type
        if date:
            cleaned_data["day_type"] = self.get_day_type(date)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set the auto-detected day type
        if hasattr(self, "cleaned_data") and "day_type" in self.cleaned_data:
            instance.day_type = self.cleaned_data["day_type"]

        if commit:
            instance.save()

            # Handle assignment updates
            assignments_data = self.cleaned_data.get("assignments_data", "")
            if assignments_data:
                import json

                try:
                    # First, remove existing assignments for this block
                    instance.assignments.all().delete()

                    # Then create new assignments from JSON data
                    assignments = json.loads(assignments_data)

                    for assignment_data in assignments:
                        assignment_type = assignment_data.get("type")
                        entity_id = assignment_data.get("entity_id")
                        notes = assignment_data.get("notes", "")

                        if assignment_type and entity_id:
                            # Create or get the entity
                            entity = self._get_or_create_entity(
                                assignment_type, entity_id
                            )

                            if entity:
                                # Get default styling from configuration
                                color, icon = self._get_default_styling(assignment_type)

                                # Create assignment
                                Assignment.objects.create(
                                    timeblock=instance,
                                    entity_type=assignment_type,
                                    entity_id=entity_id,
                                    notes=notes,
                                    color=color,
                                    icon=icon,
                                )
                except (json.JSONDecodeError, KeyError) as e:
                    # Log error but don't fail the form save
                    pass

        return instance

    def _get_or_create_entity(self, entity_type, entity_id):
        """Create or get entity based on type and ID"""
        try:
            if entity_type == "donor":
                entity, created = Donor.objects.get_or_create(donor_id=entity_id)
                return entity
            elif entity_type == "recipient":
                entity, created = Recipient.objects.get_or_create(
                    recipient_id=entity_id
                )
                return entity
            elif entity_type == "lab_task":
                entity, created = LabTask.objects.get_or_create(name=entity_id)
                return entity
        except Exception:
            pass
        return None

    def _get_default_styling(self, entity_type):
        """Get default color and icon from configuration"""
        config = ASSIGNMENT_TYPE_CONFIG.get(entity_type, {})
        return config.get("color", "primary"), config.get("icon", "bi-person-fill")

    class Meta:
        model = TimeBlock
        fields = ["date", "oncall_type", "claim"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "oncall_type": forms.RadioSelect(attrs={"class": "form-check-input"}),
            "claim": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.25",
                    "min": "0",
                    "placeholder": "0.00",
                }
            ),
        }


class TimeEntryForm(forms.ModelForm):
    detail_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        help_text="Enter detail text (optional)",
    )

    class Meta:
        model = TimeEntry
        fields = ["time_started", "time_ended", "task", "work_mode"]
        widgets = {
            "time_started": forms.TimeInput(
                attrs={"type": "time", "class": "form-control"}
            ),
            "time_ended": forms.TimeInput(
                attrs={"type": "time", "class": "form-control"}
            ),
            "task": forms.Select(attrs={"class": "form-select"}),
            "work_mode": forms.Select(attrs={"class": "form-select"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Handle detail text
        detail_text = self.cleaned_data.get("detail_text")
        if detail_text:
            detail, created = Detail.objects.get_or_create(text=detail_text)
            instance.detail = detail

        if commit:
            instance.save()
        return instance
