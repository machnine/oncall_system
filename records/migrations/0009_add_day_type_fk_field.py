# Generated manually for safe migration

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0008_populate_daytypes'),
    ]

    operations = [
        # Add new foreign key field (temporary)
        migrations.AddField(
            model_name='block',
            name='day_type_fk',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='records.daytype'),
        ),
    ]