# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0014_rename_block_to_timeblock'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='color',
            field=models.CharField(choices=[('primary', 'Primary'), ('secondary', 'Secondary'), ('success', 'Success'), ('danger', 'Danger'), ('warning', 'Warning'), ('info', 'Info'), ('light', 'Light'), ('dark', 'Dark')], default='primary', help_text='Bootstrap color for the assignment badge', max_length=20),
        ),
        migrations.AddField(
            model_name='assignment',
            name='icon',
            field=models.CharField(default='bi-person-fill', help_text='Bootstrap icon class (e.g., bi-person-fill)', max_length=50),
        ),
    ]