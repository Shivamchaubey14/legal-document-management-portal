# Generated by Django 5.2.1 on 2025-06-23 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0014_useractionlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='useractionlog',
            name='changes',
            field=models.TextField(blank=True, null=True),
        ),
    ]
