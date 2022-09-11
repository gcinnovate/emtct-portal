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



# Mother Registration Form ====================================================================================================
# from django import forms
from .models import FcappOrgunits



# creating a django form
LANGUAGE_CHOICES =(
    ("en","English" ),
    ("soga", "Lusoga"),
    ("acoli", "Acholi" ),
    ("ganda", "Luganda"),
    
)

LACTATING_CHOICES=[('pregnant','Pregnant'),
         ('lactating','Lactating')]


# class DateInput(forms.DateInput):
#     input_type = 'date'


class MotherForm(forms.Form):   
    apikey = forms.CharField(label="Your API Key",widget = forms.TextInput(attrs={'placeholder':'Please Enter Your API key'}))
    name = forms.CharField(label="Mother's name",widget = forms.TextInput(attrs={'placeholder':'Name of Mother'}))
    sex = forms.CharField(label="Sex (Mothers only)", widget = forms.TextInput(attrs={'readonly':'readonly'}))
    # sex = forms.CharField(label="Sex", widget = forms.TextInput(attrs={'readonly':'readonly', 'disabled':'disabled'}))
    phonenumber = forms.CharField(label="Contact Number (start with 256)", widget = forms.TextInput(attrs={'placeholder':'256XXXXXXXXX'}))
    # region = forms.ModelChoiceField(queryset=FcappOrgunits.objects.filter(hierarchylevel = 2).values('name'))
    region = forms.ChoiceField(choices= [('', 'Please Select Region')] + [(x['id'],x['name']) for x in FcappOrgunits.objects.filter(hierarchylevel = 2).values('id','name')])
    # region = forms.ChoiceField(choices= [('', 'Please Select Region')]) 
    district = forms.ChoiceField(choices= [('', 'Please Select District')])# + [(x['id'],x['name']) for x in FcappOrgunits.objects.filter(hierarchylevel = 2).values('id','name')])
    subcounty = forms.ChoiceField(choices= [('', 'Please Select Subcounty')])# + [(x['id'],x['name']) for x in FcappOrgunits.objects.filter(hierarchylevel = 2).values('id','name')])
    parish = forms.ChoiceField(choices= [('', 'Please Select Parish')])# + [(x['id'],x['name']) for x in FcappOrgunits.objects.filter(hierarchylevel = 2).values('id','name')])
    village = forms.CharField(widget = forms.TextInput(attrs={'placeholder':'Village of Mother'}))
    # region = forms.ChoiceField(choices= [(x['name'],x['name']) for x in FcappOrgunits.objects.filter(hierarchylevel = 2).values('name')])
    language = forms.ChoiceField(choices = LANGUAGE_CHOICES)
    like = forms.ChoiceField(label="Mother Status", choices=LACTATING_CHOICES, widget=forms.RadioSelect)
    # forms.DateField(widget=DateInput)
    # lmp = forms.DateField(label="Last Menstrual Period", widget = forms.SelectDateWidget)
    # lmp = forms.DateField(label="Last Menstrual Period", widget = DateInput)
    lmp = forms.DateField(label="Last Menstrual Period", widget=forms.DateInput(attrs={'type': 'date'}))