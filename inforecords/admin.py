from django.contrib import admin

from .models import (Profession, Contact, ContactInformation, Cluster,
                     Station, Country, PcType, Pc,
                     MonitorPulseheightThresholds,
                     MonitorService, EnabledService)


class ClusterAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'parent', 'country')
    list_filter = ('country',)
    ordering = ['number']


class ContactInline(admin.StackedInline):
    model = Contact
    extra = 0  # this stops empty forms being shown
    max_num = 0  # this removes the add more button
    can_delete = False


class StationInline(admin.StackedInline):
    model = Station
    extra = 0  # this stops empty forms being shown
    max_num = 0  # this removes the add more button
    can_delete = False


class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email_work_link')
    list_max_show_all = 400

    def last_name(self, obj):
        if obj.prefix_surname:
            return "%s, %s" % (obj.surname, obj.prefix_surname)
        else:
            return "%s" % obj.surname

    def email_work_link(self, obj):
        return "<a href='mailto:%s'>%s</a>" % (obj.email_work, obj.email_work)

    email_work_link.allow_tags = True


class CountryAdmin(admin.ModelAdmin):
    list_display = ('number', 'name')
    ordering = ['number']


class StationAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'cluster', 'contactinformation',
                    'contact')
    search_fields = ('number', 'name', 'cluster__name')
    list_filter = ('cluster__country',)
    list_per_page = 200


class ContactInformationAdmin(admin.ModelAdmin):

    def owner_name(self, obj):
        return obj.contact_owner

    list_display = ('owner_name', 'street_1', 'postalcode', 'city', 'type')
    list_filter = ('city',)
    list_max_show_all = 400

    def type(self, obj):
        return obj.type

    inlines = (ContactInline, StationInline)


class EnabledServiceInline(admin.TabularInline):
    model = EnabledService
    extra = 10


class MonitorPulseheightThresholdsAdmin(admin.ModelAdmin):
    list_display = ('station', 'plate', 'mpv_mean', 'mpv_sigma')
    list_filter = ('station',)
    list_per_page = 200


class MonitorServiceAdmin(admin.ModelAdmin):
    list_display = ('description', 'is_default_service', 'nagios_command')
    inlines = (EnabledServiceInline,)


class PcAdmin(admin.ModelAdmin):
    list_display = ('station', 'name', 'is_active', 'is_test', 'ip', 'url',
                    'keys')
    list_filter = ('is_active', 'is_test')
    ordering = ('station',)
    inlines = (EnabledServiceInline,)
    list_per_page = 200


class EnabledServiceAdmin(admin.ModelAdmin):
    list_display = ('pc', 'monitor_service', 'min_critical', 'max_critical',
                    'min_warning', 'max_warning')
    list_filter = ('pc', 'monitor_service')


admin.site.register(Profession)
admin.site.register(Contact, ContactAdmin)
admin.site.register(ContactInformation, ContactInformationAdmin)
admin.site.register(Cluster, ClusterAdmin)
admin.site.register(Station, StationAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(PcType)
admin.site.register(Pc, PcAdmin)
admin.site.register(MonitorPulseheightThresholds,
                    MonitorPulseheightThresholdsAdmin)
admin.site.register(MonitorService, MonitorServiceAdmin)
admin.site.register(EnabledService, EnabledServiceAdmin)
