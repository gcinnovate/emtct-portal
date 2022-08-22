# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.utils import timezone
from temba_client.v2 import TembaClient
from .models import *
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import pandas as pd

test_client = TembaClient('hiwa.tmcg.co.ug', 'a1db2aad0ee3c207b5128c1fc8bce312cff31b21')
contact = Contact.objects.first()
export = 'media/emtct_exports/EMTCT.xls'

class RapidProTest(TestCase):
    def test_add_rapidpro(self):
        rapidpro_instances_count = RapidPro.objects.count()
        RapidPro.add_rapidpro(name='Test Instance', host='hiwa.tmcg.co.ug', key='a1db2aad0ee3c207b5128c1fc8bce312cff31b21')
        added_rapidpro_count = RapidPro.objects.count()
        self.assertEquals(rapidpro_instances_count + 1, added_rapidpro_count)


class ContactTest(TestCase):
    def test_save_contacts(self):
        contact_count = Contact.objects.count()
        contacts_added=Contact.save_contacts(client=test_client)
        total_contacts_count = contact_count + contacts_added
        self.assertEquals(Contact.objects.count(), total_contacts_count)

class MessageTest(TestCase):
    def test_save_messages(self):
        message_count = Message.objects.count()
        messages_added = Message.save_messages(contact=contact, client=test_client )
        total_messages_count = message_count + messages_added
        self.assertEquals(Message.objects.count(), total_messages_count)

class UgandaEMRExportTest(TestCase):
    def test_sync_data(self):
        number_of_contacts_in_export = len(pd.read_excel(export))
        contacts_updates = UgandaEMRExport.sync_data(export)
        self.assertGreaterEqual(number_of_contacts_in_export, contacts_updates)




