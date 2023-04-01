# Generated by Django 3.2.18 on 2023-03-24 20:33

import bookwyrm.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('bookwyrm', '0177_merge_0174_auto_20230222_1742_0176_hashtag_support'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='citation_id',
            field=bookwyrm.models.fields.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='author',
            name='fedi_link',
            field=bookwyrm.models.fields.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='hashtag',
            name='name',
            field=bookwyrm.models.fields.CICharField(max_length=256),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='default_user_auth_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='auth.group'),
        ),
    ]
