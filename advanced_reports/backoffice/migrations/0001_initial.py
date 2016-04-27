# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-22 11:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SearchIndex',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
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
