# Generated by Django 3.2.18 on 2023-04-04 02:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookwyrm', '0184_auto_20230403_0156'),
    ]

    operations = [
        migrations.AlterField(
            model_name='connector',
            name='connector_file',
            field=models.CharField(choices=[('openlibrary', 'Openlibrary'), ('bookwyrm_connector', 'Bookwyrm Connector'), ('arxiv', 'Arxiv'), ('citation', 'Citation')], max_length=255),
        ),
    ]