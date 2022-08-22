from __future__ import absolute_import, unicode_literals
from celery import shared_task
from emtct.models import RapidPro
from datetime import datetime

now = datetime.now()

@shared_task(time = str(now))
def print_message(time, *args, **kwargs):
  print("Celery is working fine at {}.".format(time))

@shared_task()
def sync_emtct_data():
    RapidPro.sync_rapidpro()
    return print_message(time=str(now))