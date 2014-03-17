from django.contrib import admin
from django.forms import widgets
from django.contrib import messages
from django.shortcuts import redirect

from .models import Backend, Embed
from .forms import EmbedForm
from .admin_forms import EmbedFormPreview


class BackendAdmin(admin.ModelAdmin):
    list_display = ['name', 'regex', 'priority']
    readonly_fields = ['code_path']
    fieldsets = (
        ('Information', {
            'fields': ('name', 'code_path', 'description')
        }),
        ('Matching Behavior', {
            'fields': ('regex', 'priority')
        }),
    )

    # remove "Add" button
    change_list_template = 'embeds/admin/change_list_template.html'

    def formfield_for_dbfield(self, db_field, **kwargs):
        """Change the form widget for the description field"""

        formfield = super(BackendAdmin, self)\
            .formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'description':
            formfield.widget = widgets.Textarea(attrs=formfield.widget.attrs)
        return formfield

    def add_view(self, request, *args, **kwargs):
        """Override the Add view with messaging and a redirect"""

        messages.error(request, 'New Backends cannot be added via the Admin.')
        return redirect('admin:embeds_backend_changelist')


class EmbedAdmin(admin.ModelAdmin):
    list_display = ['url', 'title', 'backend_name',
                    'provider', 'type', 'cached']
    list_filter = ['backend__name', 'provider', 'type']
    search_fields = ['url', 'response_cache']

    def title(self, obj):
        return obj.response.title if obj.response else ''

    def backend_name(self, obj):
        return obj.backend.name
    backend_name.short_description = "Backend"

    def cached(self, obj):
        return bool(obj.response_cache)
    cached.boolean = True

    def get_urls(self):
        try:
            from django.conf.urls import patterns, url
        except ImportError:  # Django 1.3 # pragma: no cover
            from django.conf.urls.defaults import patterns, url

        info = self.model._meta.app_label, self.model._meta.module_name
        my_urls = patterns('',
            url(r'^add/$', EmbedFormPreview(EmbedForm, self), name='%s_%s_add' % info),
            url(r'^(\d+)/$', EmbedFormPreview(EmbedForm, self), name='%s_%s_change' % info),
        )
        return my_urls + super(EmbedAdmin, self).get_urls()


admin.site.register(Embed, EmbedAdmin)
admin.site.register(Backend, BackendAdmin)
