# Generated manually for safe migration

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0010_migrate_day_type_data'),
    ]

    operations = [
        # Remove the old CharField
        migrations.RemoveField(
            model_name='block',
            name='day_type',
        ),
        # Rename the FK field to day_type
        migrations.RenameField(
            model_name='block',
            old_name='day_type_fk',
            new_name='day_type',
        ),
    ]