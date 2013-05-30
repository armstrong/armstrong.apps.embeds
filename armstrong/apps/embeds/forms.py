from django import forms

from .models import Embed


EMBED_FORM_EXCLUDE = []


class EmbedForm(forms.ModelForm):
    class Meta:
        model = Embed
        fields = ('url', 'backend')
        exclude = EMBED_FORM_EXCLUDE

    required_css_class = 'required'  # styling for required fields

    def clean(self):
        """Auto-assign a Backend if not selected in the form"""

        self._meta.exclude = EMBED_FORM_EXCLUDE  # HACK
        cleaned_data = super(EmbedForm, self).clean()

        if not cleaned_data.get('backend'):
            url = cleaned_data.get('url', self.instance.url)
            cleaned_data['backend'] = self.instance.choose_backend(url)  # None is okay

            # KLUDGE to avoid a model error while trying to assign None
            # to the required field, temporarily exclude it
            if not url:
                self._meta.exclude = ['backend']
        return cleaned_data
