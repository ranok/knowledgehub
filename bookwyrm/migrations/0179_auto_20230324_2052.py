# Generated by Django 3.2.18 on 2023-03-24 20:52

import bookwyrm.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookwyrm', '0178_auto_20230324_2033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='connector',
            name='connector_file',
            field=models.CharField(choices=[('openlibrary', 'Openlibrary'), ('bookwyrm_connector', 'Bookwyrm Connector')], max_length=255),
        ),
        migrations.AlterField(
            model_name='edition',
            name='physical_format',
            field=bookwyrm.models.fields.CharField(blank=True, choices=[('Book', 'Book'), ('Paper', 'Paper'), ('BlogPost', 'Blog Post'), ('Talk', 'Talk'), ('SocialMediaPost', 'Social media post')], max_length=255, null=True),
        ),
    ]
