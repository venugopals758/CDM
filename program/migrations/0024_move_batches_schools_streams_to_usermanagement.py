# State-only migration: Batches/Schools/Streams moved to the usermanagement app
# (see usermanagement.migrations.0002_batches_schools_streams). The u_batches/u_schools/
# u_streams tables and the FK columns pointing at them are unchanged - only Django's
# migration state needs updating, so no database operations are issued here.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('program', '0023_rename_programbatches_batches_and_more'),
        ('usermanagement', '0002_batches_schools_streams'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='programs',
                    name='program_batch',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='usermanagement.batches'),
                ),
                migrations.AlterField(
                    model_name='programs',
                    name='school',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='usermanagement.schools'),
                ),
                migrations.AlterField(
                    model_name='programschooldurationexitplanmapping',
                    name='school',
                    field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usermanagement.schools'),
                ),
                migrations.AlterField(
                    model_name='trackheaderlevelschoolmapping',
                    name='school',
                    field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usermanagement.schools'),
                ),
                migrations.AlterField(
                    model_name='programs',
                    name='program_stream',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='usermanagement.streams'),
                ),
                migrations.DeleteModel(
                    name='Batches',
                ),
                migrations.DeleteModel(
                    name='Schools',
                ),
                migrations.DeleteModel(
                    name='Streams',
                ),
            ],
        ),
    ]
