# Generated migration to replace Detail model with TextField on TimeEntry

from django.db import migrations, models


def transfer_detail_data(apps, schema_editor):
    """Transfer data from Detail model to TimeEntry.details field"""
    TimeEntry = apps.get_model('records', 'TimeEntry')
    
    # Transfer each Detail text to the corresponding TimeEntry details field
    for time_entry in TimeEntry.objects.filter(detail__isnull=False):
        time_entry.details = time_entry.detail.text
        time_entry.save()


def reverse_transfer_detail_data(apps, schema_editor):
    """Reverse migration: recreate Detail objects from TimeEntry.details"""
    TimeEntry = apps.get_model('records', 'TimeEntry')
    Detail = apps.get_model('records', 'Detail')
    
    # Recreate Detail objects for TimeEntries that have details
    for time_entry in TimeEntry.objects.filter(details__isnull=False).exclude(details=''):
        detail, _ = Detail.objects.get_or_create(text=time_entry.details)
        time_entry.detail = detail
        time_entry.save()


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0032_alter_assignment_notes'),
    ]

    operations = [
        # Step 1: Add the new details field
        migrations.AddField(
            model_name='timeentry',
            name='details',
            field=models.TextField(blank=True, help_text='Optional details about this time entry'),
        ),
        
        # Step 2: Transfer data from Detail to details field
        migrations.RunPython(transfer_detail_data, reverse_transfer_detail_data),
        
        # Step 3: Remove the old detail foreign key
        migrations.RemoveField(
            model_name='timeentry',
            name='detail',
        ),
        
        # Step 4: Delete the Detail model
        migrations.DeleteModel(
            name='Detail',
        ),
    ]
