# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pyexcel
import os
from django.views.generic.edit import FormView
from distutils import dist
import uuid
from django.conf import settings
from django.contrib.auth.decorators import login_required
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
class BulkUpload(FormView):
    template_name = 'emtct/bulk_upload.html'
    form_class = BulkForm

    def form_invalid(self, form):
        dict1 = form.cleaned_data

        invalid_output = self.request.POST.dict()

        print("<==========================================>")
        print("<==========================================>")
        print("<==========================================>")

        print("Invalid flow")
        print("<==========================================>")
        print("<==========================================>")
        print("<==========================================>")
        print(dict1)
        print("<==========================================>")
        print("<==========================================>")
        print("<==========================================>")
        print("Invalid flow")
        print(invalid_output)
        print("<==========================================>")
        print("<==========================================>")
        print("<==========================================>")
        print(form.errors)
        return HttpResponseRedirect(reverse_lazy('bulk_upload'))

    def form_valid(self, form):
        dict1 = form.cleaned_data
        content = dict1['document']
        import subprocess
        subprocess.run(["clear"])
        print(type(content))
        # print(str(content.file.tell()))

        # print(content.get_array())
        count = 0
        # for item in content.get_array():
        #     count += 1
        #     print(count, " ", item)
        #     break
        # print(dir(pyexcel))
        # sheet = pyexcel.get_sheet(file_type="xlsx", file_content=content)
        sheet = pyexcel.Sheet()
        # print(dir(sheet))
        sheet.xlsx = content
        # sheet.csv = content
        # print(len(sheet.array))
        l = 0
        for row in sheet.array:
            count += 1
            print(count, " ", row)
            if l == 0:
                print(l, row)
                l = l+1

                continue
            else:
                print(l, row)
                print(l, 'Start Adding item...........................................')
                l = l+1
                contact_params = {
                    'name': row[1],
                    'language': None,
                    'urns': ['tel:+' + str(row[0])],
                    'groups': ['Active Receivers', 'All FC-EMTCT'],
                    'fields': {'sex': row[2],  'village': row[7], 'nin': row[3], 'sub_county': row[5], 'district': row[4], 'parish': row[6], 'registered_by': 'EMTCT Bulk Upload'}
                }
                print(contact_params)

            # # import logging

            # # import sys
            try:

                resp = destination_client.create_contact(name=contact_params['name'], language=contact_params['language'], urns=contact_params[
                    'urns'], fields=contact_params['fields'], groups=contact_params['groups'])  # .iterfetches(retry_on_rate_exceed=True)
                print(resp.uuid, " Sucesss........................................")
                submitteddata = SubmittedData.objects.create(
                    uuid=resp.uuid, contact_unit=contact_params)
                submitteddata.save()
                messages.success(
                    self.request, 'Mother has been successfully registered')
            except HTTPError as e:
                print("HTTPError ..................", str(e))
                messages.error(
                    self.request, 'Mother failed to register Contact IT administrator or Click back to Try again')

            except TembaHttpError as e:
                print("TembaHTTPError ..................", str(e))
                messages.error(
                    self.request, 'Mother failed to register Contact IT administrator or Click back to Try again')
            except TembaConnectionError as e:
                print("Temab Connection Error....................... ",
                      str(e), " ..................")
                messages.error(
                    self.request, 'Mother failed to register Contact IT administrator or Click back to Try again')

            except ConnectionResetError as e:
                print("Connect Reset Error....................... ",
                      str(e), " ..................")
                messages.error(
                    self.request, 'Mother failed to register Contact IT administrator or Click back to Try again')

            except (TembaBadRequestError, TembaNoSuchObjectError, TembaException) as ex:

                if "URN belongs to another contact" in str(ex):
                    messages.error(self.request, 'The contact ' +
                                   contact_params['urns'][0] + ' already added')
                    print("Temba Bad Error....................... ",
                          str(ex), " ..................")
                    # print("The contact  ", contact.urns, " will be reviewed later")
                    print("The contact  ",
                          contact_params['urns'][0], " is already added")
            except:
                print(
                    "Mother failed to register Contact IT administrator or Click back to Try again")

            if count == 3:
                break
        # print(type(sheet.xlsx))
        # valid_output = self.request.POST.dict()
        # print(valid_output)

        print("<==========================================>")
        print("<==========================================>")
        # print(type(sheet))
        # print(dir(content))
        print("<==========================================>")

        print("Valid......................................")
        print(dict1)

        return HttpResponseRedirect(reverse_lazy('bulk_upload'))


class MotherRegistration(FormView):
    template_name = 'emtct/mother_registration.html'
    form_class = MotherForm
    # success_message = "Mother has been registered"

    def get_initial(self):
        # call super if needed
        return {'sex': 'F'}
    # success_url = '/thanks/'
    # success_url = reverse_lazy('mother_registration')

    def form_valid(self, form):
        dict1 = form.cleaned_data
        # print(dict1)

        # provide api key
        # provide server url
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

        # print(district," == ", subcounty," === ", facility )
        # print("<------------------------------------------------>")
        contact_params = {
            'name': dict1['name'],
            'language': dict1['language'],
            'urns': ['tel:' + str(dict1['phonenumber'])],
            'groups': ['Active Receivers', 'All FC-EMTCT'],
            'fields': {'sex': dict1['sex'],  'art_number': dict1['art_number'],  'sub_county': subcounty, 'district': district, 'health_facility': facility, 'messages_to_receive': None, 'trusted_person': None, 'registered_by': 'EMTCT Portal'}
        }  # 'lmp': str(dict1['lmp']),
        # print("IP address: ",dict1['server_url'],"     API KEY ", dict1['apikey'])
        print("")
        print("")
        print("")
        print(dict1)
        print("......................")
        print("......................")
        print("......................")
        print(contact_params)
        print("......................")
        print("......................")
        # print("......................Storing in DB........................................")
        # submitteddata = SubmittedData.objects.create(contact_unit=contact_params)
        # submitteddata.save()
        # print("......................")
        # print("......................")
        # print("......................Saved in DB.............................")
        print("========================== API Mother Registration ==============================")

        # import logging

        # import sys
        try:

            resp = destination_client.create_contact(name=contact_params['name'], language=contact_params['language'], urns=contact_params[
                                                     'urns'], fields=contact_params['fields'], groups=contact_params['groups'])  # .iterfetches(retry_on_rate_exceed=True)
            print(resp.uuid, " Sucesss........................................")
            submitteddata = SubmittedData.objects.create(
                uuid=resp.uuid, contact_unit=contact_params)
            submitteddata.save()
            messages.success(
                self.request, 'Mother has been successfully registered')
        except HTTPError as e:
            print("HTTPError ..................", str(e))
            messages.error(
                self.request, 'Mother failed to register Contact IT administrator or Click back to Try again')

        except TembaHttpError as e:
            print("TembaHTTPError ..................", str(e))
            messages.error(
                self.request, 'Mother failed to register Contact IT administrator or Click back to Try again')
        except TembaConnectionError as e:
            print("Temab Connection Error....................... ",
                  str(e), " ..................")
            messages.error(
                self.request, 'Mother failed to register Contact IT administrator or Click back to Try again')

        except ConnectionResetError as e:
            print("Connect Reset Error....................... ",
                  str(e), " ..................")
            messages.error(
                self.request, 'Mother failed to register Contact IT administrator or Click back to Try again')

        except (TembaBadRequestError, TembaNoSuchObjectError, TembaException) as ex:

            if "URN belongs to another contact" in str(ex):
                messages.error(self.request, 'The contact ' +
                               contact_params['urns'][0] + ' already added')
                print("Temba Bad Error....................... ",
                      str(ex), " ..................")
                # print("The contact  ", contact.urns, " will be reviewed later")
                print("The contact  ",
                      contact_params['urns'][0], " is already added")
        except:
            print(
                "Mother failed to register Contact IT administrator or Click back to Try again")

        return HttpResponseRedirect(reverse_lazy('mother_registration'))

    def form_invalid(self, form):
        invalid_output = self.request.POST.dict()
        dict1 = form.cleaned_data

        print("<==========================================>")
        print("<==========================================>")
        print("<==========================================>")

        print("Invalid flow")
        print("<==========================================>")
        print("<==========================================>")
        print("<==========================================>")
        print(dict1)
        print("<==========================================>")
        print("<==========================================>")
        print("<==========================================>")
        print("Invalid flow")
        print(invalid_output)
        print("<==========================================>")
        print("<==========================================>")
        print("<==========================================>")
        print(form.errors)
        return HttpResponseRedirect(reverse_lazy('mother_registration'))


@login_required
def region_list(request):  # Function included here for testing purposes - Not required
    # region = FcappOrgunits.objects.filter(hierarchylevel = level['region']).values('id','name')
    region = FcappOrgunits.objects.filter(
        hierarchylevel=2).values('id', 'name')

    return JsonResponse({'data': [{'id': p['id'], 'name': p['name']} for p in region]})

    # region = FcappOrgunits.objects.raw(f'''
    #      select id, name from fcapp_orgunits where hierarchylevel = {level['region']}
    #  ''')
    # return JsonResponse({'data': [{ 'id' : p.id, 'name': p.name} for p in region]})


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
    logged_in_admin = User.get_logged_in_admin(request.user.id)
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
                email.send()
                return HttpResponseRedirect('/users')
            else:
                print(form.errors)
        else:
            form = UserForm()
    else:
        messages.warning(request, 'You do not have access to add a user.')

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
