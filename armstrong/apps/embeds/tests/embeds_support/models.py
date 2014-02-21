from django.db import models

from ...mixins import TemplatesByEmbedTypeMixin


class TypeModel(models.Model):
    slug = models.SlugField()


class Parent(models.Model, TemplatesByEmbedTypeMixin):
    response = None
    type = models.ForeignKey(TypeModel, null=True, blank=True)


class Child(Parent):
    pass
