# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pyexcel
import os
from django.views.generic.edit import FormView
from distutils import dist
import uuid
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.views.generic import DetailView, ListView, UpdateView
from emtct.forms import *
import csv
import random
from emtct.mixins import *
from django.views.generic import TemplateView
from emtct.decorator import *
import datetime
import calendar
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# ================================================================================
from .forms import MotherForm
from .models import FcappOrgunits, SubmittedData
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from temba_client.exceptions import TembaException, TembaConnectionError, TembaHttpError, TembaNoSuchObjectError, TembaBadRequestError
from requests.exceptions import HTTPError
from temba_client.v2 import TembaClient
from environs import Env
from django.contrib.auth.mixins import LoginRequiredMixin
from pathlib import Path
# from django.contrib.auth.models import User
# from .forms import CustomUserCreationForm
import time

# ==========================User Create ====================================================================


# @login_required
# @permission_required('auth.add_user', raise_exception=True)
# def create_user(request):
#     if request.method == 'POST':
#         form = CustomUserCreationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             # return redirect('users-list')
#             return HttpResponseRedirect(reverse_lazy('users-list'))
#     else:
#         form = CustomUserCreationForm()
#     return render(request, 'emtct/register_user.html', locals())
# ====================== END USER CREATE ========================================================================


env = Env()
env.read_env()
# ================SERVER ADDRESS AND API KEY=================================================================
apikey = env.str("API_KEY")
server_url = env.str("SERVER_URL")
destination_client = TembaClient(server_url, apikey)
# ===========================================================================================================
date = datetime.date.today()
start_datetime_of_current_month = datetime.datetime(date.year, date.month, 1)
end_datetime_of_current_month = datetime.datetime(
    date.year, date.month, calendar.mdays[date.month])


def generate_code():
    return str(random.randrange(100000, 999999))


@login_required()
def submit_verification(request):
    sent_code = request.session.get("sent_code", None)
    form = VerificationForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            request.session['code'] = form.cleaned_data['verification_code']
            if request.session['code'] == sent_code:
                request.session['verified_user'] = True
                return HttpResponseRedirect('/overview')
            else:
                messages.warning(
                    request, 'Please enter the verification code sent to your registered phone number.')

        else:
            print(form.errors)

    return render(request, 'emtct/verification.html', {'form': form})


@login_required()
def send_verification_code(request):
    user = request.user
    if user.sms_auth == False:
        request.session['verified_user'] = True
        return redirect('overview')

    else:
        verification_code = generate_code()
        phone_number = "tel:" + user.phone_number
        urn_list = [phone_number]
        text = "Your FamilyConnect EMTCT Portal verification code is %s " % verification_code
        RapidPro.send_message_broadcast_v2(urn_list=urn_list, message=text)
        request.session['sent_code'] = verification_code
        return HttpResponseRedirect('/submit-verification')


class Overview(TwoFactorMixin, TemplateView):
    template_name = "emtct/overview.html"

    def render_to_response(self, context, **response_kwargs):
        imports = UgandaEMRExport.get_count_exports(start_datetime_of_current_month, end_datetime_of_current_month,
                                                    self.request.user)
        imports_updated = UgandaEMRExport.get_count_exports_updated(start_datetime_of_current_month,
                                                                    end_datetime_of_current_month, self.request.user)
        imports_pending_update = UgandaEMRExport.get_count_exports_pending_update(start_datetime_of_current_month,
                                                                                  end_datetime_of_current_month,
                                                                                  self.request.user)
        monthly_imports = UgandaEMRExport.get_exports(start_datetime_of_current_month, end_datetime_of_current_month,
                                                      self.request.user)

        page = self.request.GET.get('page', 1)

        paginator = Paginator(monthly_imports, 4)
        try:
            paginated_imports = paginator.page(page)
        except PageNotAnInteger:
            paginated_imports = paginator.page(1)
        except EmptyPage:
            paginated_imports = paginator.page(paginator.num_pages)

        context = {'imports': imports, 'imports_updated': imports_updated,
                   'imports_pending_update': imports_pending_update, 'monthly_imports': monthly_imports,
                   'paginated_imports': paginated_imports}
        return self.response_class(request=self.request, template=self.get_template_names(), context=context,
                                   using=self.template_engine)


class Help(TwoFactorMixin, TemplateView):
    template_name = "emtct/help.html"


@two_factor_auth
def create_rapidpro(request):
    form = RapidProForm(data=request.POST)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('overview')
        else:
            print(form.errors)

    return render(request, 'emtct/rapidpro_form.html', {'form': form})


@two_factor_auth
def generate_emtct_export(request):
    user = request.user
    today_timestamp = datetime.datetime.today()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="EMTCT Data Import %s.csv"' % today_timestamp
    emtct_user = User.objects.get(id=user.id)
    form = EmtctExportForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            emtct_export_report = Message.get_emtct_export(start_date=start_date, end_date=end_date,
                                                           health_facility=emtct_user.health_facility.name)
            writer = csv.writer(response)
            writer.writerow(['Message ID', 'Phone', 'Follow up date', 'Type of Care', 'Outcome', 'Follow up type',
                             'ART number', 'OpenMRS ID', 'EID number', 'Health facility'])
            for row in emtct_export_report:
                writer.writerow([row.message_id, row.phone, row.follow_up_date, row.contact.group, row.outcome,
                                 row.contact.art_number, row.contact.openmrs_id, row.contact.eid_number,
                                row.contact.health_facility])
            writer.writerow([])
            return response
        else:
            form = EmtctExportForm()
    return render(request, 'emtct/emtct_export.html', locals())


# from django.contrib.messages.views import SuccessMessageMixin
# @two_factor_auth
class BulkUpload(LoginRequiredMixin, FormView):
    template_name = 'emtct/bulk_upload.html'
    form_class = BulkForm

    def form_invalid(self, form):
        dict1 = form.cleaned_data

        invalid_output = self.request.POST.dict()
        print("Invalid flow")
        print(form.errors)
        return HttpResponseRedirect(reverse_lazy('bulk_upload'))

    def form_valid(self, form):
        logged_in_user = self.request.user
        user_name = logged_in_user.get_username()
        dict1 = form.cleaned_data
        content = dict1['document']
        import subprocess
        subprocess.run(["clear"])
        count = 0
        sheet = pyexcel.Sheet()
        sheet.xlsx = content
        l = 0
        data_entries = []
        languages = {"English": "eng", "Lusoga": "xog", "Acholi": "ach", "Luganda": "lug", "Karamajongo": "kdj", "Runyoro": "run", 
                     "Runyakitara": "rar", "Kumam": "kdi", "Lango": "lao", "Lingala": "lin", "Lugbara": "lgg", "Aringa": "lua", 
                     "Madi": "grg",  "Runyankole": "nyn", "Ateso":"teo",
                     "Rukiga": "cyn"}

        for row in sheet.array:
            print(count, " ", row)
            if l == 0:
                print(l, row)
                l = l+1

                continue
            else:
                print(l, row)
                print(l, 'Start Adding item...........................................')
                l = l+1
                groups = ['All FC-EMTCT']
                emtctpreg_date = None
                emtctbirth_date = None

                if row[2]:
                    emtctpreg_date = datetime.datetime.now() - datetime.timedelta(weeks=int(row[2])) #emtct preg date  
                    
                    if (emtctpreg_date + datetime.timedelta(days=270)) > datetime.datetime.now():
                        groups.append('ART Pregnant Mothers')
                    emtctpreg_date = emtctpreg_date.strftime('%d-%m-%Y')
                    

                if  row[1]:
                    emtctbirth_date = datetime.datetime.now() - datetime.timedelta(weeks=int( row[1]) * 4) #emtct baby birth date
                    
                    if (emtctbirth_date + datetime.timedelta(days=2*365)) > datetime.datetime.now():
                        groups.append('ART Lactating Mothers')
                    emtctbirth_date = emtctbirth_date.strftime('%d-%m-%Y')

                if row[3] == "AppointmentReminder":
                    groups.append('ART Appointment Reminders')
                
                if row[3] == "HealthMessages":
                    groups.append('ART Health Messages')
             

                contact_params = {
                    'name': row[0],
                    'language': languages.get(row[6],"eng"),
                    'urns': ['tel:+' + str(row[4])],
                    'groups': groups,
                    'fields': {'pregnancy_age_at_enrollment': row[2] if row[2] else None ,'baby_age_at_enrollment': row[1] if row[1] else None ,'fc_emtct_pregnancy_date': emtctpreg_date ,'fc_emtct_baby_date': emtctbirth_date,'sex': 'F', 'trusted_person': row[5], 'art_number': row[7], 'district': row[8], 'sub_county': row[9], 'health_facility': row[10],  'registered_by': 'EMTCT Bulk Upload'}
                }
                print(contact_params)
            try:

                resp = destination_client.create_contact(name=contact_params['name'], language=contact_params['language'], urns=contact_params[
                    'urns'], fields=contact_params['fields'], groups=contact_params['groups'])  # .iterfetches(retry_on_rate_exceed=True)
                count += 1
                print(resp.uuid, " Sucesss........................................")
                submitteddata = SubmittedData.objects.create(
                    uuid=resp.uuid, contact_unit=contact_params)
                submitteddata.save()
    
            # except (TembaBadRequestError, TembaNoSuchObjectError, TembaException) as ex:

            #     if "URN belongs to another contact" in str(ex):
                    
            #         dest_contact = destination_client.get_contacts(
            #             urn=contact_params['urns'][0]).first()
            #         destination_client.update_contact(
            #             dest_contact.uuid, name=contact_params['name'], 
            #             language=contact_params['language'], urns=contact_params['urns'], 
            #             fields=contact_params['fields'], groups=contact_params['groups'])
            #         print("The contact  ",
            #           contact_params['urns'][0], " is already added now Updated")
            #         count += 1
       
            except Exception as e:
                print(
                    "Mother failed to register Contact IT administrator or Click back to Try again")
                print(str(e))
                datarow = [row[0], row[1], row[2], row[3],
                           row[4], row[5], row[6], row[7], row[8], row[9], row[10], 'failed']
                data_entries.append(datarow)
            print("****************************** THE END*************************************")

         
        messages.success(self.request,
                         'Number of Mothers Registered <b>'+str(count)+'</b>')

        # Add to error file
        if data_entries:
            
            def add_timestamp_to_filename(filename):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name, extension = os.path.splitext(filename)
                new_filename = f"{user_name}_{base_name}_{timestamp}{extension}"
                return new_filename
            
            original_filename = "errors.txt"
            new_filename = add_timestamp_to_filename(original_filename)
            base_dir = Path(settings.STATIC_ROOT)
            file_path = base_dir.joinpath(new_filename) 
            # open(file_path, 'w').close()
            # print("done********************************************************")
            with open(file_path, 'w') as f:  
                for i, item in enumerate(data_entries):
                    f.write(f"{i + 1}. {item}\n")
                f.write('\n')
                print(data_entries)

            file_link = os.path.basename(file_path)

            

            messages.error(self.request,
                           f'Click', extra_tags='safe')

        print("<==========================================>")

        print("Valid......................................")
        # url = str(reverse_lazy('emtct/bulk_upload.html'))
        
        # Return render with the template and context
        return render(self.request, 'emtct/bulk_upload.html', {'file_link': file_link})
        

        # return HttpResponseRedirect(reverse_lazy('bulk_upload'))


class MotherRegistration(FormView):
    template_name = 'emtct/mother_registration.html'
    form_class = MotherForm
    def get_initial(self):
        return {'sex': 'F'}
    

    def form_valid(self, form):
        dict1 = form.cleaned_data
        district = dict1['district']
        subcounty = dict1['subcounty']
        facility = dict1['facility']
        if dict1['district']:
            district = FcappOrgunits.objects.filter(
                id=int(dict1['district'])).values('name').first()
            district = district['name']
        if dict1['subcounty']:
            subcounty = FcappOrgunits.objects.filter(
                id=int(dict1['subcounty'])).values('name').first()
            subcounty = subcounty['name']
        if dict1['facility']:
            facility = FcappOrgunits.objects.filter(
                id=int(dict1['facility'])).values('name').first()
            facility = facility['name']
        groups = ['All FC-EMTCT']
        emtctpreg_date = None
        emtctbirth_date = None

        if dict1['number_of_weeks']:
            emtctpreg_date = datetime.datetime.now() - datetime.timedelta(weeks=int(dict1['number_of_weeks'])) #emtct preg date  
            
            if (emtctpreg_date + datetime.timedelta(days=270)) > datetime.datetime.now():
                groups.append('ART Pregnant Mothers')
            emtctpreg_date = emtctpreg_date.strftime('%d-%m-%Y')

        if  dict1['age_of_baby']:
            emtctbirth_date = datetime.datetime.now() - datetime.timedelta(weeks=int( dict1['age_of_baby']) * 4) #emtct baby birth date
            emtctbirth_date = str(emtctbirth_date)
            if (emtctbirth_date + datetime.timedelta(days=2 * 365)) > datetime.datetime.now():
                groups.append('ART Lactating Mothers')
            emtctbirth_date = emtctbirth_date.strftime('%d-%m-%Y')

        if dict1['message_to_receive'] == "AppointmentReminder":
            groups.append('ART Appointment Reminders')
        
        if dict1['message_to_receive'] == "HealthMessages":
            groups.append('ART Health Messages')




        contact_params = {
            'name': dict1['name'],
            'language': dict1['language'],
            'urns': ['tel:' + str(dict1['phonenumber'])],
            'groups': groups,
            # 'fields': {'sex': dict1['sex'],  'art_number': dict1['art_number'],  'sub_county': subcounty, 'district': district, 'health_facility': facility, 'messages_to_receive': None, 'trusted_person': None, 'registered_by': 'EMTCT Portal'}
            'fields': { 'fc_emtct_pregnancy_date': emtctpreg_date ,'fc_emtct_baby_date': emtctbirth_date ,'sex': dict1['sex'], 'baby_age_at_enrollment': dict1['age_of_baby'] if dict1['age_of_baby'] else None ,'pregnancy_age_at_enrollment': dict1['number_of_weeks'] if dict1['number_of_weeks'] else None ,'art_number': dict1['art_number'],  'sub_county': subcounty, 'district': district, 'health_facility': facility, 'messages_to_receive': None, 'trusted_person': None, 'registered_by': 'EMTCT Portal'}
     
        }  
        print(contact_params)
        print("========================== API Mother Registration ==============================")
        try:

            resp = destination_client.create_contact(name=contact_params['name'], language=contact_params['language'], urns=contact_params[
                                                     'urns'], fields=contact_params['fields'], groups=contact_params['groups'])  # .iterfetches(retry_on_rate_exceed=True)
            print(resp.uuid, " Sucesss........................................")
            submitteddata = SubmittedData.objects.create(
                uuid=resp.uuid, contact_unit=contact_params)
            submitteddata.save()
            messages.success(
                self.request, 'Mother has been successfully registered') 
        except Exception as e:
            print(
                "Mother failed to register Contact IT administrator or Click back to Try again")
            print(str(e))
        print("*************** THE END ******************************")

        return HttpResponseRedirect(reverse_lazy('mother_registration'))


@login_required
def region_list(request): 
    region = FcappOrgunits.objects.filter(
        hierarchylevel=2).values('id', 'name')

    return JsonResponse({'data': [{'id': p['id'], 'name': p['name']} for p in region]})


@login_required
def district_list(request, id):
    district = FcappOrgunits.objects.filter(parentid=id).values('id', 'name')

    return JsonResponse({'data': [{'id': p['id'], 'name': p['name']} for p in district]})


@login_required
def subcounty_list(request, id):
    subcounty = FcappOrgunits.objects.filter(parentid=id).values('id', 'name')
    return JsonResponse({'data': [{'id': p['id'], 'name': p['name']} for p in subcounty]})


@login_required
def parish_list(request, id):
    parish = FcappOrgunits.objects.filter(parentid=id).values('id', 'name')
    return JsonResponse({'data': [{'id': p['id'], 'name': p['name']} for p in parish]})


# ======================================================================================

@two_factor_auth
def import_ugandaemr_emtct_export(request):
    saved = False
    if request.method == 'POST':
        form = UgandaEMRExportForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.uploaded_by = request.user
            instance.save()
            saved = True
            export = instance.export_file
            # Update contacts in Rapidpro
            updated_contacts = UgandaEMRExport.sync_data(export=export)
            log_activity(instance, instance.uploaded_by)
    else:
        form = UgandaEMRExportForm()
    return render(request, 'emtct/emtct_import.html', locals())


@two_factor_auth
def register_user(request):

    print('beginning nowwwwwwwwwwwwwwwwwww')
    # logged_in_admin = User.get_logged_in_admin(request.user.id)
    logged_in_admin = User
    print(request.user.id)
    registered = False
    if logged_in_admin:
        if request.method == 'POST':
            form = UserForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                email_password = user.password
                user.set_password(user.password)
                user.created_by = request.user
                user.save()
                registered = True
                current_site = get_current_site(request)
                mail_subject = 'FamilyConnect EMTCT Login'
                message = render_to_string('emtct/email_user_credentials.html', {
                    'user': user,
                    'email_password': email_password,
                    'domain': current_site.domain})
                to_email = user.email
                email = EmailMessage(
                    mail_subject, message, to=[to_email]
                )
                # email.send()
                print('Middle nowwwwwwwwwwwwwwwwwww')
                return HttpResponseRedirect('/users')
            else:
                print(form.errors)
        else:
            form = UserForm()
    else:
        messages.warning(request, 'You do not have access to add a user.')
    print('End nowwwwwwwwwwwwwwwwwww')

    return render(request, 'emtct/register_user.html', locals())


class UserDetail(TwoFactorMixin, DetailView):
    login_url = '/'
    model = User
    template_name = 'emtct/user_detail.html'

    def get_context_data(self, **kwargs):
        context = super(UserDetail, self).get_context_data(**kwargs)
        context['now'] = datetime.datetime.now()
        return context


class UserList(TwoFactorMixin, ListView):
    model = User
    template_name = 'emtct/user_list.html'
    paginate_by = 8

    def get_queryset(self):
        return self.model.objects.filter(created_by=self.request.user)


class UserUpdate(TwoFactorMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email',
              'user_role', 'health_facility', 'sms_auth']
    template_name = 'emtct/user_update.html'
    success_url = '/users'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.save()
        return super(UserUpdate, self).form_valid(form)
