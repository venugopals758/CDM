# State-only migration: Batches/Schools/Streams are moving here from the program app.
# Their tables (u_batches, u_schools, u_streams) already exist from program's own rename
# migration, so this must NOT issue any CREATE TABLE - only update Django's migration state.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usermanagement', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='Batches',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=100)),
                        ('status', models.BooleanField(default=1)),
                    ],
                    options={
                        'db_table': 'u_batches',
                    },
                ),
                migrations.CreateModel(
                    name='Schools',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=500)),
                        ('code', models.CharField(max_length=50, null=True)),
                        ('status', models.BooleanField(default=1)),
                    ],
                    options={
                        'db_table': 'u_schools',
                    },
                ),
                migrations.CreateModel(
                    name='Streams',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=100)),
                        ('status', models.BooleanField(default=1)),
                    ],
                    options={
                        'db_table': 'u_streams',
                    },
                ),
            ],
        ),
    ]
