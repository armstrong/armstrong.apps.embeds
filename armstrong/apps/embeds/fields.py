from django.db import models
from django.db.models.fields.subclassing import Creator
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor


class ResetResponseMixin(object):
    """Clear the response data if this field changes"""

    def __init__(self, *args, **kwargs):
        self.response_attr = kwargs.pop('response_attr')
        super(ResetResponseMixin, self).__init__(*args, **kwargs)

    def __set__(self, instance, value):
        previous = None
        if hasattr(instance, self.field.name):
            previous = getattr(instance, self.field.name)
        super(ResetResponseMixin, self).__set__(instance, value)

        if previous and previous != value:
            delattr(instance, self.response_attr)


class SetResponseFieldMixin(object):
    def __init__(self, *args, **kwargs):
        self.response_attr = kwargs.pop('response_attr', None)
        if not self.response_attr:
            raise TypeError('%s requires a "response_attr" argument'
                            % self.__class__.__name__)
        super(SetResponseFieldMixin, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(SetResponseFieldMixin, self).contribute_to_class(cls, name)
        setattr(cls, name,
                self.descriptor_class(self, response_attr=self.response_attr))

    def deconstruct(self):  # pragma: no cover
        name, path, args, kwargs = \
            super(SetResponseFieldMixin, self).deconstruct()
        kwargs['response_attr'] = self.response_attr
        return name, path, args, kwargs


class ResetResponseDescriptor(ResetResponseMixin, Creator):
    pass


class ResetResponseFKDescriptor(ResetResponseMixin, ReverseSingleRelatedObjectDescriptor):
    pass


class EmbedURLField(SetResponseFieldMixin, models.URLField):
    descriptor_class = ResetResponseDescriptor


class EmbedForeignKey(SetResponseFieldMixin, models.ForeignKey):
    descriptor_class = ResetResponseFKDescriptor


# If South is installed, create migration rules
try:
    from south.modelsinspector import add_introspection_rules
except ImportError:  # pragma: no cover
    pass
else:
    add_introspection_rules([
        (
            [EmbedURLField, EmbedForeignKey],
            [],
            dict(response_attr=("response_attr", {}))
        )
    ], [
        "^armstrong\.apps\.embeds\.fields\.EmbedURLField",
        "^armstrong\.apps\.embeds\.fields\.EmbedForeignKey"
    ])
