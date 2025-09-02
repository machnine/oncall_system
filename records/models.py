from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, time, timedelta


class OnCallStaff(models.Model):
    assignment_id = models.CharField(max_length=50, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.assignment_id} - {self.user.get_full_name()}"


class WorkMode(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name


class Task(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name


class Detail(models.Model):
    text = models.TextField()
    
    def __str__(self):
        return self.text[:50] + "..." if len(self.text) > 50 else self.text


class Block(models.Model):
    DAY_TYPES = [
        ('Weekday', 'Weekday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
        ('BankHoliday', 'Bank Holiday'),
    ]
    
    staff = models.ForeignKey(OnCallStaff, on_delete=models.CASCADE)
    date = models.DateField()
    day_type = models.CharField(max_length=20, choices=DAY_TYPES, default='Weekday')
    claim = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Total claim hours for this block")
    created = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Removed unique_together to allow multiple blocks per day
        pass
    
    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        
        # Prevent future dates
        if self.date and self.date > timezone.now().date():
            raise ValidationError("Block date cannot be in the future.")
    
    def save(self, *args, **kwargs):
        if not self.day_type:
            if self.date.weekday() == 5:  # Saturday
                self.day_type = 'Saturday'
            elif self.date.weekday() == 6:  # Sunday
                self.day_type = 'Sunday'
            else:
                self.day_type = 'Weekday'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.staff.assignment_id} - {self.date} ({self.day_type})"


class TimeEntry(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='time_entries')
    time_started = models.TimeField()
    time_ended = models.TimeField()
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    detail = models.ForeignKey(Detail, on_delete=models.SET_NULL, null=True, blank=True)
    work_mode = models.ForeignKey(WorkMode, on_delete=models.CASCADE)
    created = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(auto_now=True)
    
    @property
    def hours(self):
        """Calculate hours worked, handling overnight blocks (17:30-08:30+1)"""
        start = datetime.combine(self.block.date, self.time_started)
        end = datetime.combine(self.block.date, self.time_ended)
        
        # If end time is before start time, it's the next day
        if self.time_ended <= self.time_started:
            end += timedelta(days=1)
            
        duration = end - start
        return round(duration.total_seconds() / 3600, 2)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Basic validation - end time should be different from start time
        if self.time_started == self.time_ended:
            raise ValidationError("Start time and end time cannot be the same.")
    
    def __str__(self):
        return f"{self.block.staff.assignment_id} - {self.block.date} - {self.task.name} ({self.hours}h)"
