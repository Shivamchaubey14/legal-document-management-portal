# Generated by Django 5.2.1 on 2025-06-13 06:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0005_amcagreement_document_pending_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='amcagreement',
            name='document_status',
            field=models.CharField(choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')], default='INCOMPLETE', max_length=20),
        ),
        migrations.AlterField(
            model_name='bmcagreement',
            name='document_status',
            field=models.CharField(choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')], default='INCOMPLETE', max_length=20),
        ),
        migrations.AlterField(
            model_name='cattlefeedagreement',
            name='document_status',
            field=models.CharField(choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')], default='INCOMPLETE', max_length=20),
        ),
        migrations.AlterField(
            model_name='consultantagreement',
            name='document_status',
            field=models.CharField(choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')], default='INCOMPLETE', max_length=20),
        ),
        migrations.AlterField(
            model_name='cookagreement',
            name='document_status',
            field=models.CharField(choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')], default='INCOMPLETE', max_length=20),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(choices=[('data_entry', 'Data Entry'), ('viewer', 'Viewer')], max_length=20),
        ),
        migrations.AlterField(
            model_name='distributeragreement',
            name='document_status',
            field=models.CharField(choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')], default='INCOMPLETE', max_length=20),
        ),
        migrations.AlterField(
            model_name='godownagreement',
            name='document_status',
            field=models.CharField(choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')], default='INCOMPLETE', max_length=20),
        ),
        migrations.AlterField(
            model_name='guesthouseagreement',
            name='document_status',
            field=models.CharField(choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')], default='INCOMPLETE', max_length=20),
        ),
        migrations.AlterField(
            model_name='mccagreement',
            name='document_status',
            field=models.CharField(choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')], default='INCOMPLETE', max_length=20),
        ),
        migrations.AlterField(
            model_name='milksaleagreement',
            name='document_status',
            field=models.CharField(choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')], default='INCOMPLETE', max_length=20),
        ),
        migrations.AlterField(
            model_name='mpacsagreement',
            name='document_status',
            field=models.CharField(choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')], default='INCOMPLETE', max_length=20),
        ),
        migrations.AlterField(
            model_name='officeleaseagreement',
            name='document_status',
            field=models.CharField(choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')], default='INCOMPLETE', max_length=20),
        ),
        migrations.AlterField(
            model_name='rentalbmcagreement',
            name='document_status',
            field=models.CharField(choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')], default='INCOMPLETE', max_length=20),
        ),
        migrations.AlterField(
            model_name='rtaagreement',
            name='document_status',
            field=models.CharField(choices=[('INCOMPLETE', 'INCOMPLETE'), ('COMPLETE', 'COMPLETE'), ('EXPIRE', 'EXPIRE')], default='INCOMPLETE', max_length=20),
        ),
    ]
