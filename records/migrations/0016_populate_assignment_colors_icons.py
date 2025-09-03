# Generated manually
from django.db import migrations


def populate_assignment_colors_icons(apps, schema_editor):
    Assignment = apps.get_model('records', 'Assignment')
    
    # Default mappings
    color_map = {
        'donor': 'success',
        'recipient': 'info', 
        'lab_task': 'warning'
    }
    
    icon_map = {
        'donor': 'bi-person-fill',
        'recipient': 'bi-person-down',
        'lab_task': 'bi-thermometer-low'
    }
    
    # Update existing assignments
    for assignment in Assignment.objects.all():
        assignment.color = color_map.get(assignment.entity_type, 'primary')
        assignment.icon = icon_map.get(assignment.entity_type, 'bi-person-fill')
        assignment.save()


def reverse_populate_assignment_colors_icons(apps, schema_editor):
    # No reverse operation needed
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0015_add_assignment_color_icon'),
    ]

    operations = [
        migrations.RunPython(
            populate_assignment_colors_icons,
            reverse_populate_assignment_colors_icons,
        ),
    ]