# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-07 03:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emtct', '0006_auto_20181106_0600'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='sms_auth',
            field=models.BooleanField(default=True),
        ),
    ]
