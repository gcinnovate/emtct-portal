from django import forms
from emtct.models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit


class UserForm(forms.ModelForm):
    password = forms.CharField(min_length=6, max_length=30)
    phone_number = forms.CharField(max_length=13, min_length=13, help_text='+2567XXXXXXXX')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'email', 'password', 'user_role', 'health_facility')
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
