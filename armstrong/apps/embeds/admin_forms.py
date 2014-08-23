from functools import wraps

from django.core.cache import cache
from django.utils.translation import ugettext as _
from django.contrib.formtools.preview import FormPreview

try:
    from django.db.transaction import atomic
except ImportError:  # DROP_WITH_DJANGO15 # pragma: no cover
    from django.db.transaction import commit_on_success as atomic
try:
    from django.utils.encoding import force_text
except ImportError:  # DROP_WITH_DJANGO13 # pragma: no cover
    from django.utils.encoding import force_unicode as force_text
try:
    from django.utils.text import slugify
except ImportError:  # DROP_WITH_DJANGO14 # pragma: no cover
    from django.template.defaultfilters import slugify

from .models import Embed
from .backends import InvalidResponseError


def generate_cache_key(backend, url):
    cache_key = "armstrong.apps.embeds-response-for-%s-%s" % \
        (backend.pk, slugify(unicode(url)))
    return cache_key[:250]  # memcached max key length


# TODO relocate to a shared location
# TODO if Django updates this class to use class-based Views
# (as they did with FormWizard in Django 1.4) this will need to change, though
# some things (such as admin_view() wrapping) will be dramatically easier
class AdminFormPreview(FormPreview):
    """
    Adapt FormPreview into the Admin replacing the normal add/change views
    with a two-step process for editing a Model and previewing before save.

    """
    def __init__(self, form, admin):
        super(AdminFormPreview, self).__init__(form)
        self.admin = admin
        self.model = self.admin.model
        self.object_id = None
        self.object = None
        self.action = "add"

        self.admin.add_form_template = self.form_template
        self.admin.change_form_template = self.preview_template

    def __call__(self, request, *args, **kwargs):
        """Wrap the FormPreview in Admin decorators"""

        # Change View if we've been passed an object_id
        if len(args) >= 1:
            from django.contrib.admin.util import unquote

            self.object_id = args[0]
            self.action = "change"
            self.object = self.admin.get_object(request, unquote(self.object_id))

        method = super(AdminFormPreview, self).__call__
        method = self.perm_check(method)
        method = self.admin.admin_site.admin_view(method)
        return method(request, *args, **kwargs)

    def perm_check(self, func):
        """Provide permissions checking normally handled in add_view() and change_view()"""

        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if self.object_id and not self.object:
                from django.utils.html import escape
                from django.http import Http404
                raise Http404(
                    _('%(name)s object with primary key %(key)r does not exist.') %
                    {'name': force_text(self.model._meta.verbose_name),
                     'key': escape(self.object_id)})

            from django.core.exceptions import PermissionDenied
            if self.action == "add" and not self.admin.has_add_permission(request):
                raise PermissionDenied
            elif not self.admin.has_change_permission(request, self.object):
                raise PermissionDenied

            return func(request, *args, **kwargs)
        return wrapper

    def get_context(self, request, form):
        """Provide templates vars expected by the Admin change_form.html"""

        opts = self.model._meta
        context = super(AdminFormPreview, self).get_context(request, form)
        context.update(dict(
            title=_('%s %s') % (self.action.title(), force_text(opts.verbose_name)),
            object_id=self.object_id,
            original=self.object,
            is_popup="_popup" in request.REQUEST,
            current_app=self.admin.admin_site.name,
            show_delete=(self.action == "change"),
            app_label=opts.app_label,
            opts=opts,
            #
            # Other context vars present in the Admin add_view/change_view--
            # Not entirely sure how or if its appropriate to use these
            # so acknowledge them and make it clear we aren't using them
            #
            # adminform -- our stuff is not an AdminForm
            # media -- collection of ModelAdmin, AdminForm and inline formset media
            inline_admin_formsets=[],  # we know this should be empty
            # errors -- AdminErrorList, combines all form and formset errors
        ))
        return context

    def get_render_change_form_params(self, request):
        return dict(
            obj=self.object,
            add=(self.action == 'add'),
            change=(self.action == 'change'))

    def preview_get(self, request):
        """
        Displays the form.
        Overriden to provide the model instance instead of initial data
        and call the Admin's render_change_form().

        """
        f = self.form(auto_id=self.get_auto_id(), instance=self.object)
        context = self.get_context(request, f)
        render_params = self.get_render_change_form_params(request)
        return self.admin.render_change_form(request, context, **render_params)

    def preview_post(self, request):
        """
        Validates the POST data. If valid, displays the preview page, else
        redisplays form. Overriden to
          - provide the model instance
          - use Admin's render_change_form()
          - update the title context var
          - provide a "step2" context var letting us share a single tempate

        """
        f = self.form(request.POST, auto_id=self.get_auto_id(), instance=self.object)
        context = self.get_context(request, f)

        if f.is_valid():
            self.process_preview(request, f, context)
            context.update(dict(
                is_step2=True,
                title=_('Preview %s') % force_text(context['opts'].verbose_name),
                hash_field=self.unused_name('hash'),
                hash_value=self.security_hash(request, f)))

        render_params = self.get_render_change_form_params(request)
        return self.admin.render_change_form(request, context, **render_params)

    def post_post(self, request):
        """
        Validates the POST data. If valid, calls done(). Else, redisplays form.
        Overriden to
          - supply the form model instance
          - call preview_post() instead of calling its own render
          - add transaction support

        """
        f = self.form(request.POST, auto_id=self.get_auto_id(), instance=self.object)
        if f.is_valid():
            if not self._check_security_hash(request.POST.get(self.unused_name('hash'), ''),
                                             request, f):
                return self.failed_hash(request)  # Security hash failed

            with atomic():
                return self.done(request, f.cleaned_data)
        else:
            return self.preview_post(request)


class EmbedFormPreview(AdminFormPreview):
    """
    A replacement for the normal Admin edit views that provides a two-step
    process for editing an Embed object. Since so much of the Embed data
    is gathered from an API, we want to present that to the user so they
    have an idea what they are creating.

    """
    form_template = "embeds/admin/embed_change_form.html"
    preview_template = "embeds/admin/embed_change_form.html"

    def _set_error(self, form, msg):
        """Insert error messages into the form"""

        from django.utils.safestring import mark_safe
        from django.forms.forms import NON_FIELD_ERRORS

        if NON_FIELD_ERRORS not in form._errors:  # pragma: no cover
            form._errors[NON_FIELD_ERRORS] = form.error_class()
        form._errors[NON_FIELD_ERRORS].append(mark_safe(msg))

    def process_preview(self, request, form, context):
        """
        Generate the response (and cache it) or provide error messaging.
        Update the form with the auto-assigned Backend if necessary.

        """
        try:
            response = form.instance.get_response()
            if not response.is_valid():
                # throw an error so we can share the except block logic
                raise InvalidResponseError(response._data)
        except InvalidResponseError as e:
            msg = "Invalid response from the Backend API.<br />\
                Check the URL for typos and/or try a different Backend."
            self._set_error(form, msg)

            try:  # handle dict data masquerading as an Exception string
                from ast import literal_eval
                error_dict = literal_eval(str(e))
            except (ValueError, SyntaxError):  # just use the string
                error_dict = dict(data=e)

            error_dict['exception'] = type(e).__name__
            context['response_error'] = error_dict
        else:
            context['duplicate_response'] = (form.instance.response == response)
            form.instance.response = response

            # cache the response to prevent another API call on save
            # set() overwrites if anything already exists from another attempt
            cache_key = generate_cache_key(
                form.instance.backend, form.instance.url)
            cache.set(cache_key, form.instance.response_cache, 300)

        #HACK if the backend was auto-assigned the form field must also be set
        if not form.data['backend']:
            data = form.data.copy()  # mutable QueryDict
            backends = list(form.fields['backend']._queryset)
            data['backend'] = backends.index(form.instance.backend) + 1  # select box options are 1-indexed
            form.data = data

    def done(self, request, cleaned_data):
        """Save Embed using cached response to avoid another API call"""

        # get or create the object and use form data
        embed = self.object if self.object else Embed()
        embed.url = cleaned_data['url']
        embed.backend = cleaned_data['backend']

        # load and use cached response then delete/clean up
        cache_key = generate_cache_key(embed.backend, embed.url)
        embed.response = embed.backend.wrap_response_data(cache.get(cache_key), fresh=True)
        cache.delete(cache_key)

        # save and continue with the Admin Site workflow
        embed.save()
        return self.admin.response_add(request, embed)

    def get_context(self, request, form):
        context = super(EmbedFormPreview, self).get_context(request, form)
        context['errornote_css_class'] = 'errornote'
        context['form1_submit_text'] = "Request new data & Preview" if self.action == "change" else "Preview"
        return context
