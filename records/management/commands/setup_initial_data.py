from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from records.models import OnCallStaff, WorkMode, Task


class Command(BaseCommand):
    help = 'Set up initial data for the oncall system'

    def handle(self, *args, **options):
        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Created superuser: admin/admin123'))

        # Create initial WorkModes
        work_modes = ['WFH', 'Lab']
        for mode_name in work_modes:
            mode, created = WorkMode.objects.get_or_create(name=mode_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created WorkMode: {mode_name}'))

        # Create initial Tasks
        tasks = [
            'Donor offer',
            'SAB',
            'Phone call',
            'matching run',
            'VXM',
            'travel time',
            'SAB assay (inc collecting blood from ward)',
            'issue VXM',
        ]
        for task_name in tasks:
            task, created = Task.objects.get_or_create(name=task_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created Task: {task_name}'))

        # Create a sample staff member
        if not OnCallStaff.objects.exists():
            user = User.objects.create_user('john_doe', 'john@example.com', 'password123')
            user.first_name = 'John'
            user.last_name = 'Doe'
            user.save()
            
            staff = OnCallStaff.objects.create(assignment_id='JD001', user=user)
            self.stdout.write(self.style.SUCCESS(f'Created OnCallStaff: {staff}'))

        self.stdout.write(self.style.SUCCESS('Initial data setup completed!'))