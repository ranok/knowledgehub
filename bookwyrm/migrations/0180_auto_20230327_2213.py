# Generated by Django 3.2.18 on 2023-03-27 22:13

import bookwyrm.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bookwyrm', '0179_auto_20230324_2052'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='citation_id',
            field=bookwyrm.models.fields.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='book',
            name='url',
            field=bookwyrm.models.fields.TextField(blank=True, max_length=255, null=True),
        ),
    ]