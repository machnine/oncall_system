#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from records.models import OnCallStaff, RotaShift

print("=== OnCallStaff Records ===")
staff = OnCallStaff.objects.all()
print(f'Total staff: {staff.count()}')
for s in staff:
    print(f'{s.assignment_id}: seniority_level={s.seniority_level}')

print("\n=== RotaShift Records ===")
shifts = RotaShift.objects.all()[:10]  # First 10 shifts
print(f'Total shifts: {RotaShift.objects.count()}')
for shift in shifts:
    print(f'Shift {shift.id}: staff={shift.staff.assignment_id}, seniority={shift.seniority_level}')
