# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SearchIndex',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('backoffice_instance', models.CharField(max_length=32)),
                ('model_slug', models.CharField(max_length=32)),
                ('model_id', models.PositiveIntegerField()),
                ('to_index', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'search index entry',
                'verbose_name_plural': 'search index entries',
            },
        ),
    ]
