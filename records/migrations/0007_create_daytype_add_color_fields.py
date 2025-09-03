# Generated manually for safe migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0006_remove_timeentry_claim'),
    ]

    operations = [
        # Create DayType model
        migrations.CreateModel(
            name='DayType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('color', models.CharField(choices=[('primary', 'Primary (Blue)'), ('secondary', 'Secondary (Gray)'), ('success', 'Success (Green)'), ('danger', 'Danger (Red)'), ('warning', 'Warning (Yellow)'), ('info', 'Info (Cyan)'), ('light', 'Light'), ('dark', 'Dark')], default='info', max_length=20)),
            ],
        ),
        # Add color field to Task
        migrations.AddField(
            model_name='task',
            name='color',
            field=models.CharField(choices=[('primary', 'Primary (Blue)'), ('secondary', 'Secondary (Gray)'), ('success', 'Success (Green)'), ('danger', 'Danger (Red)'), ('warning', 'Warning (Yellow)'), ('info', 'Info (Cyan)'), ('light', 'Light'), ('dark', 'Dark')], default='secondary', max_length=20),
        ),
        # Add color field to WorkMode
        migrations.AddField(
            model_name='workmode',
            name='color',
            field=models.CharField(choices=[('primary', 'Primary (Blue)'), ('secondary', 'Secondary (Gray)'), ('success', 'Success (Green)'), ('danger', 'Danger (Red)'), ('warning', 'Warning (Yellow)'), ('info', 'Info (Cyan)'), ('light', 'Light'), ('dark', 'Dark')], default='primary', max_length=20),
        ),
    ]