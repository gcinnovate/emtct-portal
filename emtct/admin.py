# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.contrib import admin
from emtct.models import *
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportMixin, ImportMixin, ExportActionModelAdmin, ImportExportActionModelAdmin



class RapidProAdmin(admin.ModelAdmin):
    list_display = [f.name for f in RapidPro._meta.get_fields()]
    list_filter = ['created_at', 'updated_at']


class UserAdmin(admin.ModelAdmin):
    list_display = ['id','first_name', 'last_name', 'phone_number', 'email', 'user_role', 'health_facility', 'is_active',
                    'is_superuser', 'is_staff', 'created_at', 'created_by', 'updated_at', 'updated_by', 'last_login']
    list_filter = ['created_at', 'updated_at']


class ContactAdmin(admin.ModelAdmin):
    list_display = ['uuid','phone', 'group', 'last_visit_date', 'next_appointment', 'health_facility']
    list_filter = ['created_at', 'updated_at', 'group']

class MessageAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Message._meta.get_fields()]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['text']


class UgandaEMRExportAdmin(admin.ModelAdmin):
    list_display = ['export_file', 'sync_status', 'uploaded_by', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']


class HealthFacilityResource(resources.ModelResource):
    class Meta:
        model = HealthFacility
        fields = ('name', 'parish', 'sub_county', 'county', 'region','district')
        exclude = ('id', 'created_at', 'updated_at')
        import_id_fields = ('name', 'parish', 'sub_county', 'county', 'region','district')
        skip_unchanged = True
        report_skipped = True

class HealthFacilityAdmin(ImportMixin, admin.ModelAdmin):
    resource_class = HealthFacilityResource
    list_display = ['id','name', 'parish', 'sub_county', 'county', 'region','district', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name']


admin.site.register(RapidPro, RapidProAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(HealthFacility, HealthFacilityAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(UgandaEMRExport, UgandaEMRExportAdmin)

