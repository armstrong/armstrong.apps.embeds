from django.db import models

from armstrong.apps.embeds.mixins import TemplatesByEmbedTypeMixin
from armstrong.apps.embeds.fields import EmbedURLField


class TypeModel(models.Model):
    slug = models.SlugField()

    class Meta:
        app_label = 'armstrong.apps.embeds'


class Parent(models.Model, TemplatesByEmbedTypeMixin):
    response = None
    type = models.ForeignKey(TypeModel, null=True, blank=True)

    class Meta:
        app_label = 'armstrong.apps.embeds'


class Child(Parent):
    class Meta:
        app_label = 'armstrong.apps.embeds'


class CustomFieldModel(models.Model):
    field = EmbedURLField(response_attr="response")

    class Meta:
        app_label = 'armstrong.apps.embeds'

    def __init__(self, *args, **kwargs):
        super(CustomFieldModel, self).__init__(*args, **kwargs)
        self.response = "testing"
