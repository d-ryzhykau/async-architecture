# Generated by Django 4.2.6 on 2023-11-03 18:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tasks", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="jira_id",
            field=models.CharField(blank=True, max_length=24),
        ),
    ]