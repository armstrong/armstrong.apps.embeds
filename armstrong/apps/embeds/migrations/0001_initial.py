# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import armstrong.apps.embeds.fields
import model_utils.fields
import armstrong.apps.embeds.mixins
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Backend',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('code_path', models.CharField(help_text=b'Full Python path for the actual Backend code.', unique=True, max_length=100)),
                ('description', models.CharField(max_length=255, null=True, blank=True)),
                ('regex', models.CharField(help_text=b'Used to match a URL when automatically assigning backends.', max_length=100)),
                ('priority', models.PositiveSmallIntegerField(default=1, help_text=b'A higher number means higher priority. Used when automatically assigning a backend.')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Embed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', armstrong.apps.embeds.fields.EmbedURLField(unique=True, response_attr=b'response')),
                ('response_cache', django_extensions.db.fields.json.JSONField()),
                ('response_last_updated', model_utils.fields.MonitorField(default=None, null=True, monitor=b'response_cache', blank=True)),
                ('backend', armstrong.apps.embeds.fields.EmbedForeignKey(blank=True, response_attr=b'response', to='embeds.Backend', help_text=b'The most appropriate Backend will auto-assign if not explicitly provided')),
            ],
            options={
            },
            bases=(models.Model, armstrong.apps.embeds.mixins.TemplatesByEmbedTypeMixin),
        ),
        migrations.CreateModel(
            name='EmbedType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Automatically populated by the backends', unique=True, max_length=25, editable=False)),
                ('slug', models.SlugField(help_text=b'Used as a folder name in the template lookup.', unique=True, max_length=25, editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Provider',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'Automatically populated by the backends', unique=True, max_length=50, editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='embed',
            name='provider',
            field=models.ForeignKey(blank=True, to='embeds.Provider', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='embed',
            name='type',
            field=models.ForeignKey(blank=True, to='embeds.EmbedType', null=True),
            preserve_default=True,
        ),
    ]
