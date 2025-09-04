# Generated manually to add oncall_type field to TimeBlock

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0019_rename_task_to_tasktype'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeblock',
            name='oncall_type',
            field=models.CharField(
                choices=[('normal', 'Normal'), ('nhsp', 'NHSP')], 
                default='normal', 
                help_text='Type of on-call duty', 
                max_length=20
            ),
        ),
    ]
