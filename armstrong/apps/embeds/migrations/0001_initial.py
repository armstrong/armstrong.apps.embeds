# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Backend'
        db.create_table(u'embeds_backend', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('code_path', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('regex', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
        ))
        db.send_create_signal(u'embeds', ['Backend'])

        # Adding model 'Provider'
        db.create_table(u'embeds_provider', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
        ))
        db.send_create_signal(u'embeds', ['Provider'])

        # Adding model 'EmbedType'
        db.create_table(u'embeds_embedtype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=25)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=25)),
        ))
        db.send_create_signal(u'embeds', ['EmbedType'])

        # Adding model 'Embed'
        db.create_table(u'embeds_embed', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('armstrong.apps.embeds.fields.EmbedURLField')(response_attr='response', max_length=200, unique=True)),
            ('backend', self.gf('armstrong.apps.embeds.fields.EmbedForeignKey')(to=orm['embeds.Backend'], response_attr='response', blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['embeds.EmbedType'], null=True, blank=True)),
            ('provider', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['embeds.Provider'], null=True, blank=True)),
            ('response_cache', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('response_last_updated', self.gf('model_utils.fields.MonitorField')(default=None, null=True, monitor='response_cache', blank=True)),
        ))
        db.send_create_signal(u'embeds', ['Embed'])


    def backwards(self, orm):
        # Deleting model 'Backend'
        db.delete_table(u'embeds_backend')

        # Deleting model 'Provider'
        db.delete_table(u'embeds_provider')

        # Deleting model 'EmbedType'
        db.delete_table(u'embeds_embedtype')

        # Deleting model 'Embed'
        db.delete_table(u'embeds_embed')


    models = {
        u'embeds.backend': {
            'Meta': {'object_name': 'Backend'},
            'code_path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'priority': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'regex': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'embeds.embed': {
            'Meta': {'object_name': 'Embed'},
            'backend': ('armstrong.apps.embeds.fields.EmbedForeignKey', [], {'to': u"orm['embeds.Backend']", 'response_attr': "'response'", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['embeds.Provider']", 'null': 'True', 'blank': 'True'}),
            'response_cache': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'response_last_updated': ('model_utils.fields.MonitorField', [], {'default': 'None', 'null': 'True', 'monitor': "'response_cache'", 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['embeds.EmbedType']", 'null': 'True', 'blank': 'True'}),
            'url': ('armstrong.apps.embeds.fields.EmbedURLField', [], {'response_attr': "'response'", 'max_length': '200', 'unique': 'True'})
        },
        u'embeds.embedtype': {
            'Meta': {'object_name': 'EmbedType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '25'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '25'})
        },
        u'embeds.provider': {
            'Meta': {'object_name': 'Provider'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        }
    }

    complete_apps = ['embeds']
