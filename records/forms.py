from django import forms
from django.utils import timezone
from govuk_bank_holidays.bank_holidays import BankHolidays
from .models import Block, TimeEntry, Detail


class BlockForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date to today if this is a new form (no instance)
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()
        
        # Set max date to today for client-side validation
        today = timezone.now().date().isoformat()
        self.fields['date'].widget.attrs['max'] = today
    
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise forms.ValidationError("Block date cannot be in the future.")
        return date
    
    def get_day_type(self, date):
        """Automatically determine day type based on date using official UK government data"""
        if not date:
            return None
            
        # Get UK bank holidays from official government data
        bank_holidays = BankHolidays()
        uk_holidays = bank_holidays.get_holidays('england-and-wales', date.year)
        
        # Create a set of holiday dates for efficient lookup
        holiday_dates = {holiday['date'] for holiday in uk_holidays}
        
        # Check if it's a bank holiday
        if date in holiday_dates:
            return 'Bank Holiday'
        
        # Check day of week (Monday=0, Sunday=6)
        weekday = date.weekday()
        
        if weekday < 5:  # Monday-Friday (0-4)
            return 'Weekday'
        elif weekday == 5:  # Saturday
            return 'Saturday'
        else:  # Sunday
            return 'Sunday'
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        
        # Auto-detect and set day type
        if date:
            cleaned_data['day_type'] = self.get_day_type(date)
            
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set the auto-detected day type
        if hasattr(self, 'cleaned_data') and 'day_type' in self.cleaned_data:
            instance.day_type = self.cleaned_data['day_type']
        
        if commit:
            instance.save()
        return instance
    
    class Meta:
        model = Block
        fields = ['date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class BlockEditForm(forms.ModelForm):
    """Form for editing existing blocks - includes claim field"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set max date to today for client-side validation
        today = timezone.now().date().isoformat()
        self.fields['date'].widget.attrs['max'] = today
    
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise forms.ValidationError("Block date cannot be in the future.")
        return date
    
    def get_day_type(self, date):
        """Automatically determine day type based on date using official UK government data"""
        if not date:
            return None
            
        # Get UK bank holidays from official government data
        bank_holidays = BankHolidays()
        uk_holidays = bank_holidays.get_holidays('england-and-wales', date.year)
        
        # Create a set of holiday dates for efficient lookup
        holiday_dates = {holiday['date'] for holiday in uk_holidays}
        
        # Check if it's a bank holiday
        if date in holiday_dates:
            return 'Bank Holiday'
        
        # Check day of week (Monday=0, Sunday=6)
        weekday = date.weekday()
        
        if weekday < 5:  # Monday-Friday (0-4)
            return 'Weekday'
        elif weekday == 5:  # Saturday
            return 'Saturday'
        else:  # Sunday
            return 'Sunday'
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        
        # Auto-detect and set day type
        if date:
            cleaned_data['day_type'] = self.get_day_type(date)
            
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set the auto-detected day type
        if hasattr(self, 'cleaned_data') and 'day_type' in self.cleaned_data:
            instance.day_type = self.cleaned_data['day_type']
        
        if commit:
            instance.save()
        return instance
    
    class Meta:
        model = Block
        fields = ['date', 'claim']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'claim': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0', 'placeholder': '0.00'}),
        }


class TimeEntryForm(forms.ModelForm):
    detail_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text="Enter detail text (optional)"
    )
    
    class Meta:
        model = TimeEntry
        fields = ['time_started', 'time_ended', 'task', 'work_mode']
        widgets = {
            'time_started': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'time_ended': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'task': forms.Select(attrs={'class': 'form-select'}),
            'work_mode': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Handle detail text
        detail_text = self.cleaned_data.get('detail_text')
        if detail_text:
            detail, created = Detail.objects.get_or_create(text=detail_text)
            instance.detail = detail
        
        if commit:
            instance.save()
        return instance