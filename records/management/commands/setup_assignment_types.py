from django.core.management.base import BaseCommand
from records.models import AssignmentType


class Command(BaseCommand):
    help = 'Create default AssignmentType records'

    def handle(self, *args, **options):
        # Create the three default assignment types
        types_data = [
            {
                'name': 'Donor',
                'code': 'donor',
                'color': 'success',
                'icon': 'bi-person-fill',
                'description': 'Blood/organ donor assignments'
            },
            {
                'name': 'Recipient', 
                'code': 'recipient',
                'color': 'info',
                'icon': 'bi-person-down',
                'description': 'Blood/organ recipient assignments'
            },
            {
                'name': 'Lab Task',
                'code': 'lab_task', 
                'color': 'warning',
                'icon': 'bi-thermometer-low',
                'description': 'Laboratory task assignments'
            }
        ]
        
        created_count = 0
        for data in types_data:
            assignment_type, created = AssignmentType.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created AssignmentType: {assignment_type.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'AssignmentType already exists: {assignment_type.name}')
                )
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} AssignmentType records')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('All AssignmentType records already exist')
            )