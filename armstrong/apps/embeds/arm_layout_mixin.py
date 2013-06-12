"""
If armstrong.core.arm_layout is being used in this project, provide a
mixin that will let our Embed Model look for templates based on Type.

"""
try:
    from armstrong.core.arm_layout.backends.mixins import ModelPathBaseMixin
except ImportError:
    class TemplatesByResponseTypeMixin(object):
        pass
else:
    class TemplatesByResponseTypeMixin(ModelPathBaseMixin):
        def __init__(self, *args, **kwargs):
            super(TemplatesByResponseTypeMixin, self).__init__(*args, **kwargs)
            self.fallback_template_name = 'default'
            self.templates_without_fallbacks = []

        def get_layout_template_name(self, name):
            specific = []
            general = []

            # Invalid responses use a fallback template under the assumption
            # that response data required by the template is unavailable
            if not self.response or not self.response.is_valid():
                if name not in self.templates_without_fallbacks:
                    name = self.fallback_template_name

            for a in self.__class__.mro():
                base_path = self._build_model_path(a)
                if not base_path:
                    continue

                if self.type:
                    specific.append("%s%s/%s.html" %
                        (base_path, self.type.name.lower(), name))
                general.append("%s%s.html" % (base_path, name))

            return specific + general
