from django.db import models
from django.db.models.fields.subclassing import Creator
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor


class ResetResponseMixin(object):
    """Clear the response data if this field changes"""

    def __init__(self, *args, **kwargs):
        self.response_field = kwargs.pop('response_field')
        super(ResetResponseMixin, self).__init__(*args, **kwargs)

    def __set__(self, instance, value):
        previous = None
        if hasattr(instance, self.field.name):
            previous = getattr(instance, self.field.name)
        super(ResetResponseMixin, self).__set__(instance, value)

        if previous and previous != value:
            delattr(instance, self.response_field)


class SetResponseFieldMixin(object):
    def __init__(self, *args, **kwargs):
        self.response_field = kwargs.pop('response_field', None)
        if not self.response_field:
            raise TypeError(
                '%s requires a "response_field" argument' % self.__class__.__name__)
        super(SetResponseFieldMixin, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(SetResponseFieldMixin, self).contribute_to_class(cls, name)
        setattr(cls, name, self.descriptor_class(self, response_field=self.response_field))


class ResetResponseDescriptor(ResetResponseMixin, Creator):
    pass


class ResetResponseFKDescriptor(ResetResponseMixin, ReverseSingleRelatedObjectDescriptor):
    pass


class EmbedURLField(SetResponseFieldMixin, models.URLField):
    descriptor_class = ResetResponseDescriptor


class EmbedForeignKey(SetResponseFieldMixin, models.ForeignKey):
    descriptor_class = ResetResponseFKDescriptor


from south.modelsinspector import add_introspection_rules
add_introspection_rules([
    (
        [EmbedURLField, EmbedForeignKey],
        [],
        dict(response_field=("response_field", {}))
    )
], [
    "^armstrong\.apps\.embeds\.fields\.EmbedURLField",
    "^armstrong\.apps\.embeds\.fields\.EmbedForeignKey"
])
