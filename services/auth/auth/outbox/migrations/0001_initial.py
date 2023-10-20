# Generated by Django 4.2.5 on 2023-09-30 19:45

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("topic", models.CharField(max_length=255)),
                ("name", models.CharField(max_length=255)),
                ("version", models.PositiveSmallIntegerField()),
                ("key", models.CharField(max_length=255)),
                ("data", models.JSONField()),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "event",
            },
        ),
    ]