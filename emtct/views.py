# -*- coding: utf-8 -*-
from __future__ import unicode_literals
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
#================================================================================
from .forms import MotherForm
from .models import FcappOrgunits
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
#=================================================================================





date = datetime.date.today()
start_datetime_of_current_month = datetime.datetime(date.year, date.month, 1)
end_datetime_of_current_month =  datetime.datetime(date.year, date.month, calendar.mdays[date.month])

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
                messages.warning(request, 'Please enter the verification code sent to your registered phone number.')

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

            context = {'imports': imports, 'imports_updated':imports_updated,
                       'imports_pending_update':imports_pending_update, 'monthly_imports':monthly_imports,
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

    return render(request, 'emtct/rapidpro_form.html', {'form': form })


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
            writer =csv.writer(response)
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
    return  render(request, 'emtct/emtct_export.html', locals())

from django.views.generic.edit import FormView
# @two_factor_auth
class MotherRegistration(FormView):
    template_name = 'emtct/mother_registration.html'
    form_class = MotherForm
    

    def get_initial(self):
         # call super if needed
         return {'sex': 'Female'}
    success_url = '/thanks/'
    success_url = reverse_lazy('mother_registration')

    def form_valid(self, form):
        dict1=form.cleaned_data
        apikey = dict1['apikey']

        contact_params={
            'name': dict1['name'],
            'language': dict1['language'],
            'urns': ['tel:+' + dict1['phonenumber']],
            'groups': ['Active Receivers', 'Type = Child', 'Type = VHT', 'Type = Nurse', 'Type = ReproductiveAge', 'Type =      Midwife', 'Reproductive Age', 'Registered VHTs', 'Update Contact With Incorrect District', 'Incorrect District And Village', 'Update Reproductive Registrations'],
            'fields': {'sex': dict1['sex'], 'lmp': str(dict1['lmp']), 'village': None,  'sub_county': None, 'district': None, 'parish': None}
        }
        print(dict1)
        return HttpResponseRedirect(reverse_lazy('mother_registration'))
        # return  render(request, 'emtct/mother_registration.html', locals())


@login_required
def region_list(request): # Function included here for testing purposes - Not required 
    # region = FcappOrgunits.objects.filter(hierarchylevel = level['region']).values('id','name') 
    region = FcappOrgunits.objects.filter(hierarchylevel = 2).values('id','name')
    
    return JsonResponse({'data': [{ 'id' : p['id'], 'name': p['name']} for p in region]})
    
    # region = FcappOrgunits.objects.raw(f'''
    #      select id, name from fcapp_orgunits where hierarchylevel = {level['region']}
    #  ''')
    # return JsonResponse({'data': [{ 'id' : p.id, 'name': p.name} for p in region]})



@login_required
def district_list(request, id):
    district = FcappOrgunits.objects.filter(parentid = id).values('id','name')
    
    return JsonResponse({'data': [{ 'id' : p['id'], 'name': p['name']} for p in district]})


@login_required
def subcounty_list(request, id):
    subcounty = FcappOrgunits.objects.filter(parentid = id).values('id','name')
    return JsonResponse({'data': [{ 'id' : p['id'], 'name': p['name']} for p in subcounty]})


@login_required
def parish_list(request, id):
    parish = FcappOrgunits.objects.filter(parentid = id).values('id','name')
    return JsonResponse({'data': [{ 'id' : p['id'], 'name': p['name']} for p in parish]})


#======================================================================================

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
            ## Update contacts in Rapidpro
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
                    'domain': current_site.domain })
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
    fields = ['first_name', 'last_name', 'email', 'user_role', 'health_facility', 'sms_auth']
    template_name = 'emtct/user_update.html'
    success_url = '/users'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.save()
        return super(UserUpdate, self).form_valid(form)






