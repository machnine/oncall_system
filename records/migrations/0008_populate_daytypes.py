# Generated manually for safe migration

from django.db import migrations


def populate_daytypes(apps, schema_editor):
    DayType = apps.get_model('records', 'DayType')
    
    # Create the standard day types
    DayType.objects.create(name='Weekday', color='success')
    DayType.objects.create(name='Saturday', color='warning') 
    DayType.objects.create(name='Sunday', color='danger')
    DayType.objects.create(name='BankHoliday', color='info')


def remove_daytypes(apps, schema_editor):
    DayType = apps.get_model('records', 'DayType')
    DayType.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0007_create_daytype_add_color_fields'),
    ]

    operations = [
        migrations.RunPython(populate_daytypes, remove_daytypes),
    ]