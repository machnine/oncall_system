# Generated manually for safe migration

from django.db import migrations


def migrate_day_type_data(apps, schema_editor):
    Block = apps.get_model('records', 'Block')
    DayType = apps.get_model('records', 'DayType')
    
    # Create mapping from string to DayType objects
    day_type_mapping = {}
    for day_type in DayType.objects.all():
        day_type_mapping[day_type.name] = day_type
    
    # Migrate all blocks
    for block in Block.objects.all():
        if block.day_type and block.day_type in day_type_mapping:
            block.day_type_fk = day_type_mapping[block.day_type]
            block.save()


def reverse_migrate_day_type_data(apps, schema_editor):
    Block = apps.get_model('records', 'Block')
    
    # Clear the foreign key field
    for block in Block.objects.all():
        block.day_type_fk = None
        block.save()


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0009_add_day_type_fk_field'),
    ]

    operations = [
        migrations.RunPython(migrate_day_type_data, reverse_migrate_day_type_data),
    ]