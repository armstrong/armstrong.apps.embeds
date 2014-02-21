"""
If armstrong.core.arm_layout is being used in this project, provide a
mixin that will let our Embed Model look for templates based on EmbedType.

"""
try:
    from armstrong.core.arm_layout.mixins import TemplatesByTypeMixin
except ImportError:
    class TemplatesByEmbedTypeMixin(object):
        pass
else:
    class TemplatesByEmbedTypeMixin(TemplatesByTypeMixin):
        fallback_template_name = 'default'

        def __init__(self, *args, **kwargs):
            self.templates_without_fallbacks = []
            super(TemplatesByEmbedTypeMixin, self).__init__(*args, **kwargs)

        def get_layout_template_name(self, name):
            """
            Look up templates by the embed instance type.

            Designed for use with ArmLayout's ModelProvidedLayoutBackend.
            If the embed instance has a valid response, then there will be a
            response type presumably with type-specific data to use in the
            template. So we look for templates based on type.

            Invalid responses won't have a type so look for a template only
            on the Embed model. Unless the sought-after template is excluded,
            invalid responses will use a fallback template under the assumption
            that response data required by the template is unavailable.

            ex: "embedtype/photo/template.html"
                "embed/template.html"
            It will not include "embedtype/template.html".

            """
            if not self.response or not self.response.is_valid():
                if name not in self.templates_without_fallbacks:
                    name = self.fallback_template_name

                # normal model inheritance lookup
                ret = []
                for a in self.__class__.mro():
                    if not hasattr(a, "_meta"):
                        continue
                    base_path = self._build_model_path(a)
                    ret.append("%s%s.html" % (base_path, name))
                return ret

            return super(TemplatesByEmbedTypeMixin, self).get_layout_template_name(name)
