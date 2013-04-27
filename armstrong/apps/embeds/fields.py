from django.db import models
from django.db.models.fields.subclassing import Creator
from django.db.models.fields.related import ReverseSingleRelatedObjectDescriptor


class SetBackendDescriptor(Creator):
    """
    Clear the response data if this field changes and assign
    a Backend when this field is initially set.

    """
    def __init__(self, *args, **kwargs):
        self.assign_func = kwargs.pop('assign_func')
        self.response_field = kwargs.pop('response_field')
        super(SetBackendDescriptor, self).__init__(*args, **kwargs)

    def __set__(self, instance, value):
        previous = instance.__dict__.get(self.field.name, None)
        super(SetBackendDescriptor, self).__set__(instance, value)

        if value and not previous and not instance.pk:
            getattr(instance, self.assign_func)()

        if previous and previous != value:
            delattr(instance, self.response_field)


class ResetResponseDescriptor(ReverseSingleRelatedObjectDescriptor):
    """
    Clear the response data if this field changes and do everything
    else a ReverseSingleRelatedObjectDescriptor does.

    """
    def __init__(self, *args, **kwargs):
        self.response_field = kwargs.pop('response_field')
        super(ResetResponseDescriptor, self).__init__(*args, **kwargs)

    def __set__(self, instance, value):
        previous = None
        if hasattr(instance, self.field.name):
            previous = getattr(instance, self.field.name)
        super(ResetResponseDescriptor, self).__set__(instance, value)

        if previous and previous != value:
            delattr(instance, self.response_field)


class SetResponseFieldMixin(object):
    def __init__(self, *args, **kwargs):
        self.response_field = kwargs.pop('response_field', None)
        if not self.response_field:
            raise TypeError(
                '%s requires a "response_field" argument' % self.__class__.__name__)
        super(SetResponseFieldMixin, self).__init__(*args, **kwargs)


class EmbedURLField(SetResponseFieldMixin, models.URLField):
    descriptor_class = SetBackendDescriptor

    def __init__(self, *args, **kwargs):
        self.assign_func = kwargs.pop('assign_func', None)
        if not self.assign_func:
            raise TypeError(
                '%s requires a "assign_func" argument' % self.__class__.__name__)
        super(EmbedURLField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(EmbedURLField, self).contribute_to_class(cls, name)
        setattr(cls, name, self.descriptor_class(
                                self,
                                assign_func=self.assign_func,
                                response_field=self.response_field))


class EmbedForeignKey(SetResponseFieldMixin, models.ForeignKey):
    descriptor_class = ResetResponseDescriptor

    def contribute_to_class(self, cls, name):
        super(EmbedForeignKey, self).contribute_to_class(cls, name)
        setattr(cls, name, self.descriptor_class(self, response_field=self.response_field))
