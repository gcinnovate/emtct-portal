# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2022-04-06 19:19
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emtct', '0011_auto_20220406_1253'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rapidpro',
            old_name='sms_channel',
            new_name='sms_flow',
        ),
    ]