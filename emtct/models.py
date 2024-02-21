# -*- coding: utf-8 -*-
from __future__ import unicode_literals
# from tkinter import CASCADE
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.core.mail import send_mail
from django.db import models
from django.contrib.auth.models import PermissionsMixin
from temba_client.v2 import TembaClient
import pandas as pd
from timeline_logger.models import TimelineLog
from datetime import datetime, timedelta
from django.contrib import messages
import requests
import json

USER_ROLE = (
    ('data_clerk', 'Data Clerk'),
    ('admin', 'Administrator'),
    ('sno', 'SNO'),
    ('no', 'NO'),
    ('smo', 'SMO'),
    ('hia', 'HIA'),
    ('sro', 'SRO'),
    ('dhe', 'DHE'),
    ('dhi', 'DHI'),
    ('biostat', 'Biostat'),
    ('pmtct_fp', 'PMTCT FP'),
    ('adho', 'ADHO'),
    ('mo', 'MO'),
    ('hmis_officer', 'HMIS Officer'),
    ('data_assistant', 'Data Assistant'),
    ('enrolled_midwife', 'Enrolled Midwife'),
    ('records_officer ', 'Records Officer'),
    ('enrolled_midwife', 'Enrolled Midwife'),
    ('registered_midwives', 'Registered Midwives'),
    ('HMIS_officers ', 'HMIS Officers '),
    ('Counselor', 'Counselor'),
    ('Clinical Officer', 'Clinical Officer'),
    ('Generic User', 'Generic User')
)

yesterday = (datetime.now() - timedelta(days=1)).isoformat()
emtct_appointment_reminder_groups = [
    'ART Appointment Reminders', 'ART EID Appointment Reminders']
emtct_appointment_reminder_message_start = ['remind']


def log_activity(content_object, user):
    return TimelineLog.objects.create(content_object=content_object, user=user)


class RapidPro(models.Model):
    name = models.CharField(max_length=50)
    host = models.CharField(max_length=50)
    key = models.CharField(max_length=50)
    sms_flow = models.CharField(max_length=36)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=True)

    class Meta:
        verbose_name = 'RapidPro'
        verbose_name_plural = 'RapidPro'
        ordering = ('-created_at',)

    def __unicode__(self):
        return self.name

    @classmethod
    def add_rapidpro(cls, name, host, key):
        if RapidPro.objects.count() == 0:
            rapidpro = RapidPro.objects.create(name=name, host=host, key=key)
            return rapidpro.save()
        else:
            return 'Only supports one RapidPro instance'

    @classmethod
    def sync_rapidpro(cls):
        rapidpro = cls.objects.first()
        client = TembaClient(rapidpro.host, rapidpro.key)
        Contact.save_contacts(client=client)
        return 'Complete'

    @classmethod
    def get_rapidpro_client(cls):
        rapidpro = cls.objects.first()
        return TembaClient(rapidpro.host, rapidpro.key)

    @classmethod
    def send_message_broadcast(cls, urn_list, message):
        client = RapidPro.get_rapidpro_client()
        return client.create_broadcast(urns=urn_list, text=message)

    @classmethod
    def send_message_broadcast_v2(cls, urn_list, message):
        rapidpro = cls.objects.first()
        payload = {
            "flow": rapidpro.sms_flow,
            "urns": urn_list,
            "params": {"text": message}
        }
        try:
            response = requests.post(
                rapidpro.host + "/api/v2/flow_starts.json",
                json.dumps(payload),
                headers={
                    'Content-type': 'application/json',
                    'Authorization': 'Token %s' % rapidpro.key}
            )
        except:
            print("ERROR Sending Broadcast")


class HealthFacility(models.Model):
    name = models.CharField(max_length=100)
    parish = models.CharField(max_length=50, null=True, blank=True)
    sub_county = models.CharField(max_length=50, null=True, blank=True)
    county = models.CharField(max_length=50, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=30, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=True)

    class Meta:
        verbose_name = 'Health Facility'
        verbose_name_plural = 'Health Facilities'
        ordering = ('name',)

    # def __unicode__(self):
    #     return self.name

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('sms_auth', False)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, null=True)
    phone_number = models.CharField(max_length=13, null=False)
    email = models.EmailField(unique=True, max_length=100, null=False)
    user_role = models.CharField(max_length=36, null=False, choices=USER_ROLE)
    health_facility = models.ForeignKey(
        HealthFacility, null=True, blank=True, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    sms_auth = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    created_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='creator')
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)
    updated_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='updater')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ('-created_at', 'user_role')

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    def email_user(self, subject, message, from_email, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def email_admin(self, subject, message, **kwargs):
        send_mail(subject, message, settings.EMAIL_HOST_USER,
                  [self.created_by.email], **kwargs)

    @classmethod
    def get_logged_in_admin(cls, user_id):
        return cls.objects.filter(user_role='admin', id=user_id)


class UgandaEMRExport(models.Model):
    export_file = models.FileField(upload_to="emtct_exports")
    sync_status = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=True)

    class Meta:
        verbose_name = 'Uganda EMR Export'
        verbose_name_plural = 'Uganda EMR Exports'
        ordering = ('-created_at',)

    def __unicode__(self):
        return unicode(self.export_file)

    @classmethod
    def sync_data(cls, export=None):
        exports = cls.objects.filter(
            sync_status=False, export_file=export).all()
        update_contacts = 0
        for export in exports:
            df = pd.read_excel(export.export_file)

            for index, row in df.iterrows():
                urn = "tel:+" + str(row['Phone'])
                Contact.update_emtct_contact(urn=urn, name=row['Name'], last_visit_date=str(row['Last-Visit-Date']),
                                             next_appointment_date=str(
                                                 row['Next-Appointment-Date']),
                                             encounter_type=row['Encounter-Type'], patient_id=row['ART-Number'],
                                             openmrs_id=row['OpenMRS-ID'], eid_number=row['EID-Number'], sex=row['Sex'],
                                             birth_date=str(row['Birth-Date']), age_years=row['Age-Years'],
                                             health_facility=row['Health-Facility'])
                update_contacts += 1

            export.sync_status = True
            export.save()

        return update_contacts

    @classmethod
    def get_exports(cls, start_date, end_date, user):
        return cls.objects.filter(uploaded_by=user, created_at__range=(start_date, end_date)).all()

    @classmethod
    def get_count_exports(cls, start_date, end_date, user):
        return cls.objects.filter(uploaded_by=user, created_at__range=(start_date, end_date)).count()

    @classmethod
    def get_count_exports_updated(cls, start_date, end_date, user):
        return cls.objects.filter(uploaded_by=user, sync_status=True, created_at__range=(start_date, end_date)).count()

    @classmethod
    def get_count_exports_pending_update(cls, start_date, end_date, user):
        return cls.objects.filter(uploaded_by=user, sync_status=False, created_at__range=(start_date, end_date)).count()


class Contact(models.Model):
    uuid = models.CharField(max_length=45)
    phone = models.CharField(max_length=50)
    name = models.CharField(max_length=50, null=True)
    group = models.CharField(max_length=50)
    last_visit_date = models.DateTimeField(null=True)
    next_appointment = models.DateTimeField(null=True)
    encounter_type = models.CharField(max_length=50, null=True)
    art_number = models.CharField(max_length=50, null=True)
    openmrs_id = models.CharField(max_length=50, null=True)
    eid_number = models.CharField(max_length=50, null=True)
    sex = models.CharField(max_length=50, null=True)
    birth_date = models.CharField(max_length=50, null=True)
    age_years = models.CharField(max_length=50, null=True)
    health_facility = models.CharField(max_length=50, null=True)
    uganda_emr_export = models.ForeignKey(
        UgandaEMRExport, null=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=True)

    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        ordering = ('-created_at',)

    def __unicode__(self):
        return self.phone

    @classmethod
    def save_contacts(cls, client):
        contacts_added = 0
        for group in emtct_appointment_reminder_groups:
            for contact_batch in client.get_contacts(group=group, after=yesterday).iterfetches(retry_on_rate_exceed=True):
                for contact in contact_batch:
                    if cls.contact_exists(contact):
                        cls.objects.filter(uuid=contact.uuid).update(phone=cls.clean_contact(contact),
                                                                     name=contact.name,
                                                                     group=group,
                                                                     last_visit_date=contact.fields.get(
                                                                         'last_visit_date'),
                                                                     next_appointment=contact.fields.get(
                                                                         'next_appointment_date'),
                                                                     encounter_type=contact.fields.get(
                                                                         'encounter_type'),
                                                                     art_number=contact.fields.get(
                                                                         'patient_id'),
                                                                     openmrs_id=contact.fields.get(
                                                                         'openmrs_id'),
                                                                     eid_number=contact.fields.get(
                                                                         'eid_number'),
                                                                     sex=contact.fields.get(
                                                                         'sex'),
                                                                     birth_date=contact.fields.get(
                                                                         'birth_date'),
                                                                     age_years=contact.fields.get(
                                                                         'age_years'),
                                                                     health_facility=contact.fields.get
                                                                     ('health_facility'))

                    else:
                        cls.objects.create(uuid=contact.uuid, name=contact.name,
                                           phone=cls.clean_contact(contact), group=group,
                                           last_visit_date=contact.fields.get(
                                               'last_visit_date'),
                                           next_appointment=contact.fields.get(
                                               'next_appointment_date'),
                                           encounter_type=contact.fields.get(
                                               'encounter_type'),
                                           art_number=contact.fields.get(
                                               'patient_id'),
                                           openmrs_id=contact.fields.get(
                                               'openmrs_id'),
                                           eid_number=contact.fields.get(
                                               'eid_number'),
                                           sex=contact.fields.get('sex'),
                                           birth_date=contact.fields.get(
                                               'birth_date'),
                                           age_years=contact.fields.get(
                                               'age_years'),
                                           health_facility=contact.fields.get
                                           ('health_facility'))
                        contacts_added += 1

                    contact = Contact.objects.get(uuid=contact.uuid)
                    Message.save_messages(contact=contact, client=client)

        return contacts_added

    @classmethod
    def contact_exists(cls, contact):
        return cls.objects.filter(uuid=contact.uuid).exists()

    @classmethod
    def clean_contact(cls, contact):
        for phone_number in contact.urns:
            if 'tel:' in phone_number:
                return phone_number[4:]
            else:
                return contact.urns

    @classmethod
    def update_emtct_contact(cls, urn, name, last_visit_date, next_appointment_date, encounter_type, patient_id,
                             openmrs_id, eid_number, sex, birth_date, age_years, health_facility):
        client = RapidPro.get_rapidpro_client()
        return client.update_contact(urn, name=name, fields=dict(next_appointment_date=next_appointment_date,
                                                                 last_visit_date=last_visit_date,
                                                                 encounter_type=encounter_type, patient_id=patient_id,
                                                                 openmrs_id=openmrs_id, eid_number=eid_number, sex=sex,
                                                                 birth_date=birth_date, age_years=age_years,
                                                                 health_facility=health_facility))


class Message(models.Model):
    message_id = models.IntegerField()
    phone = models.CharField(max_length=50)
    follow_up_date = models.DateTimeField()
    outcome = models.CharField(max_length=30)
    text = models.CharField(max_length=250)
    label = models.CharField(max_length=250, null=True, blank=True)
    contact = models.ForeignKey(Contact, null=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=True)

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ('-created_at',)

    def __unicode__(self):
        return self.phone + " " + self.text

    @classmethod
    def save_messages(cls, contact, client):
        messages_added = 0

        for message_batch in client.get_messages(contact=contact.uuid, after=yesterday).iterfetches(
                retry_on_rate_exceed=True):
            for message in message_batch:
                if not cls.message_exists(message):
                    cls.objects.create(message_id=message.id, phone=cls.clean_message_phone(message),
                                       follow_up_date=message.sent_on, outcome=message.status, text=message.text,
                                       label=message.labels, contact=contact)
                    messages_added += 1
                else:
                    cls.objects.filter(message_id=message.id).update(phone=cls.clean_message_phone(message),
                                                                     follow_up_date=message.sent_on,
                                                                     outcome=message.status, text=message.text,
                                                                     label=message.labels, contact=contact)

        return messages_added

    @classmethod
    def message_exists(cls, message):
        return cls.objects.filter(message_id=message.id).exists()

    @classmethod
    def clean_message_phone(cls, message):
        if message.urn is not None and 'tel:' in message.urn:
            return message.urn[4:]
        else:
            return message.urn

    @classmethod
    def get_emtct_export(cls, start_date, end_date, health_facility):
        return cls.objects.filter(follow_up_date__range=(start_date, end_date),
                                  text__icontains=emtct_appointment_reminder_message_start,
                                  contact__health_facility__icontains=health_facility).all()

# ================LOCATION======================================


class FcappOrgunits(models.Model):
    uid = models.CharField(max_length=11)
    name = models.CharField(max_length=230)
    code = models.CharField(max_length=50)
    shortname = models.CharField(max_length=50, blank=True, null=True)
    parentid = models.BigIntegerField(blank=True, null=True)
    path = models.CharField(max_length=255, blank=True, null=True)
    hierarchylevel = models.IntegerField(blank=True, null=True)
    created = models.DateTimeField()
    updated = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'fcapp_orgunits'


class SubmittedData(models.Model):
    uuid = models.CharField(max_length=45)
    contact_unit = models.JSONField()
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=True)
