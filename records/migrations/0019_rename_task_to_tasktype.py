# Generated manually to rename Task to TaskType

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0018_rename_block_assignment_timeblock_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Task',
            new_name='TaskType',
        ),
    ]
