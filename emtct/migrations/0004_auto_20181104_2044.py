# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-04 17:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emtct', '0003_auto_20181103_0750'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='last_visit_date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='next_appointment',
            field=models.DateTimeField(null=True),
        ),
    ]
