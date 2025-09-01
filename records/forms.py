from django import forms
from django.utils import timezone
from .models import Shift, TimeEntry, Detail


class ShiftForm(forms.ModelForm):
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
            raise forms.ValidationError("Shift date cannot be in the future.")
        return date
    
    class Meta:
        model = Shift
        fields = ['date', 'day_type']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'day_type': forms.Select(attrs={'class': 'form-select'}),
        }


class TimeEntryForm(forms.ModelForm):
    detail_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        help_text="Enter detail text (optional)"
    )
    
    class Meta:
        model = TimeEntry
        fields = ['time_started', 'time_ended', 'task', 'work_mode', 'claim']
        widgets = {
            'time_started': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'time_ended': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'task': forms.Select(attrs={'class': 'form-select'}),
            'work_mode': forms.Select(attrs={'class': 'form-select'}),
            'claim': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0'}),
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