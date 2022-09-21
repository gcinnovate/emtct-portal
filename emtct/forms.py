from django import forms
from django.forms import ChoiceField
from phonenumber_field.formfields import PhoneNumberField

from emtct.models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit


class UserForm(forms.ModelForm):
    password = forms.CharField(min_length=6, max_length=30)
    phone_number = forms.CharField(
        max_length=13, min_length=13, help_text='+2567XXXXXXXX')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'email',
                  'password', 'user_role', 'health_facility')
        Layout(
            Fieldset('first_name', 'last_name')
        )


class RapidProForm(forms.ModelForm):
    class Meta:
        model = RapidPro
        fields = ['name', 'host', 'key']


class HealthFacilityForm(forms.ModelForm):
    class Meta:
        model = HealthFacility
        fields = ['name', 'parish', 'sub_county', 'county', 'district']


class UgandaEMRExportForm(forms.ModelForm):
    class Meta:
        model = UgandaEMRExport
        fields = ['export_file']


class DateTimeInput(forms.DateTimeInput):
    input_type = 'date'


class EmtctExportForm(forms.Form):
    start_date = forms.DateField(required=True)
    end_date = forms.DateField(required=True)

    class Meta:
        widgets = {'start_date': DateTimeInput(), 'end_date': DateTimeInput()}


class VerificationForm(forms.Form):
    verification_code = forms.CharField(max_length=6)


# Mother Registration Form ====================================================================================================
# from django import forms
# from .models import FcappOrgunits,


# creating a django form
LANGUAGE_CHOICES = (
    ("eng", "English"),
    ("xog", "Lusoga"),
    ("ach", "Acholi"),
    ("lug", "Luganda"),
    ("alz", "Alur"),
    ("nyn", "Nyankole"),
    ("teo", "Teso"),
    ("kdj", "Karamojong"),
    ("lgg", "Lugbara"),
    ("kdi", "Kumam"),
    ("lao", "Lao"),
    ("rar", "Rarotongan"),
    ("lin", "Lingala"),
    ("rom", "Romany"),
    ("run", "Rundi"),
    ("lua", "Luba-Lulua"),
    ("grg", "Madi"),
    ("cym", "Welsh"),
    ("nau", "Nauru"),
)


FAVORITE_COLORS_CHOICES = [
    ('blue', 'Blue'),
    ('green', 'Green'),
    ('black', 'Black'),
]


LACTATING_CHOICES = [('', "Please Select Mother's Condition"),
                     ('pregnant', 'ART Pregnant'),
                     ('lactating', 'ART Lactating')]

MESSAGE_TO_RECEIVE = [('AppointmentReminder', 'Appointment Reminders Only'),
                      ('HealthMessages', 'Health Message and Appointment Reminder')]


# custom ChoiceField and override to skip validation
class ChoiceFieldNoValidation(ChoiceField):
    def validate(self, value):
        pass


class MotherForm(forms.Form):
    # baby_age_at_enrollment
    name = forms.CharField(label="Mother's name", widget=forms.TextInput(
        attrs={'placeholder': 'Name of Mother'}))
    sex = forms.CharField(widget=forms.HiddenInput())
    mothers_condition = forms.ChoiceField(
        label="Mother's Current Status",  choices=LACTATING_CHOICES)
    number_of_weeks = forms.IntegerField(label="How many weeks is the pregnancy?", widget=forms.TextInput(
        attrs={'placeholder': 'Number of weeks'}))
    age_of_baby = forms.IntegerField(label="How many months old is the baby?", widget=forms.TextInput(
        attrs={'placeholder': 'Number of Months'}))
    message_to_receive = forms.ChoiceField(
        label="What content would like to receive?", choices=MESSAGE_TO_RECEIVE)
    phonenumber = forms.CharField(label="Mother's Phone Number (start with 256)",
                                  widget=forms.TextInput(attrs={'placeholder': '256XXXXXXXXX'}))
    # phonenumber = PhoneNumberField(region='UG', label="Mother's Contact (start with +256)",
    #    widget=forms.TextInput(attrs={'placeholder': '+256XXXXXXXXX'}))
    # trusted_person = PhoneNumberField(region='UG', required=False, label="Trusted Person Phone Number (start with +256)",
    #   widget=forms.TextInput(attrs={'placeholder': '+256XXXXXXXXX'}))
    language = forms.ChoiceField(choices=LANGUAGE_CHOICES)
    art_number = forms.CharField(label="What is Patient's ART number", widget=forms.TextInput(
        attrs={'placeholder': 'ART number'}))

    # sex = forms.CharField(label="Sex", widget = forms.TextInput(attrs={'readonly':'readonly', 'disabled':'disabled'}))

    # region = forms.ModelChoiceField(queryset=FcappOrgunits.objects.filter(hierarchylevel = 2).values('name'))
    region = forms.ChoiceField(required=False, choices=[('', 'Please Select Region')] + [(
        x['id'], x['name']) for x in FcappOrgunits.objects.filter(hierarchylevel=2).values('id', 'name')])
    # region = forms.ChoiceField(choices= [('', 'Please Select Region')])
    # + [(x['id'],x['name']) for x in FcappOrgunits.objects.filter(hierarchylevel = 2).values('id','name')])
    district = ChoiceFieldNoValidation(
        required=False, choices=[('', 'Please Select District')])
    # + [(x['id'],x['name']) for x in FcappOrgunits.objects.filter(hierarchylevel = 2).values('id','name')])
    subcounty = ChoiceFieldNoValidation(
        required=False, choices=[('', 'Please Select Subcounty')])
    # + [(x['id'],x['name']) for x in FcappOrgunits.objects.filter(hierarchylevel = 2).values('id','name')])
    facility = ChoiceFieldNoValidation(label="Health Facility", required=False, choices=[
                                       ('', 'Please Select Facility')])
    # village = forms.CharField(required=False, widget = forms.TextInput(attrs={'placeholder':'Village of Mother'}))
    # region = forms.ChoiceField(choices= [(x['name'],x['name']) for x in FcappOrgunits.objects.filter(hierarchylevel = 2).values('name')])

    # like = forms.ChoiceField(label="Mother Status", choices=LACTATING_CHOICES, widget=forms.RadioSelect)
    # favorite_colors = forms.MultipleChoiceField(
    #     required=False,
    #     widget=forms.CheckboxSelectMultiple,
    #     choices=FAVORITE_COLORS_CHOICES,
    # )

    # forms.DateField(widget=DateInput)
    # lmp = forms.DateField(label="Last Menstrual Period", widget = forms.SelectDateWidget)
    # lmp = forms.DateField(label="Last Menstrual Period", widget = DateInput)
    # lmp = forms.DateField(label="Last Menstrual Period", widget=forms.DateInput(attrs={'type': 'date'}))
    # server_url = forms.CharField(label="Server Address",widget = forms.TextInput(attrs={'placeholder':'Please Enter Your Server Address'}))
    # apikey = forms.CharField(label="Your API Key",widget = forms.TextInput(attrs={'placeholder':'Please Enter Your API key'}))
