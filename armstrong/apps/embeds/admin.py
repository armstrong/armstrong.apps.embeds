from django.contrib import admin
from django.forms import widgets
from django.contrib import messages

from .models import Backend


class BackendAdmin(admin.ModelAdmin):
    list_display = ['name', 'regex', 'priority']
    readonly_fields = ['slug']
    fieldsets = (
        ('Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Matching Behavior', {
            'fields': ('regex', 'priority')
        }),
    )

    # remove "Add" button
    change_list_template = 'embeds/admin/change_list_template.html'

    def formfield_for_dbfield(self, db_field, **kwargs):
        """Change the form widget for the description field"""

        formfield = super(BackendAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'description':
            formfield.widget = widgets.Textarea(attrs=formfield.widget.attrs)
        return formfield

    def add_view(self, request, *args, **kwargs):
        """Override the Add view with messaging and a redirect"""

        from django.shortcuts import redirect
        messages.error(request, 'New Embed backends cannot be added via the Admin.')
        return redirect('admin:embeds_backend_changelist')


admin.site.register(Backend, BackendAdmin)
