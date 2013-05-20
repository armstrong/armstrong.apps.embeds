# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Backend'
        db.create_table('embeds_backend', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('regex', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
        ))
        db.send_create_signal('embeds', ['Backend'])

        # Adding model 'Provider'
        db.create_table('embeds_provider', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
        ))
        db.send_create_signal('embeds', ['Provider'])

        # Adding model 'Type'
        db.create_table('embeds_type', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=25)),
        ))
        db.send_create_signal('embeds', ['Type'])

        # Adding model 'Embed'
        db.create_table('embeds_embed', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('armstrong.apps.embeds.fields.EmbedURLField')(response_field='response', max_length=200, unique=True, assign_func='_auto_assign_backend')),
            ('backend', self.gf('armstrong.apps.embeds.fields.EmbedForeignKey')(to=orm['embeds.Backend'], response_field='response')),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['embeds.Type'], null=True, blank=True)),
            ('provider', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['embeds.Provider'], null=True, blank=True)),
            ('response_cache', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('response_last_updated', self.gf('model_utils.fields.MonitorField')(default=None, null=True, monitor='response_cache', blank=True)),
        ))
        db.send_create_signal('embeds', ['Embed'])


    def backwards(self, orm):
        # Deleting model 'Backend'
        db.delete_table('embeds_backend')

        # Deleting model 'Provider'
        db.delete_table('embeds_provider')

        # Deleting model 'Type'
        db.delete_table('embeds_type')

        # Deleting model 'Embed'
        db.delete_table('embeds_embed')


    models = {
        'embeds.backend': {
            'Meta': {'object_name': 'Backend'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'priority': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'regex': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'embeds.embed': {
            'Meta': {'object_name': 'Embed'},
            'backend': ('armstrong.apps.embeds.fields.EmbedForeignKey', [], {'to': "orm['embeds.Backend']", 'response_field': "'response'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['embeds.Provider']", 'null': 'True', 'blank': 'True'}),
            'response_cache': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'response_last_updated': ('model_utils.fields.MonitorField', [], {'default': 'None', 'null': 'True', 'monitor': "'response_cache'", 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['embeds.Type']", 'null': 'True', 'blank': 'True'}),
            'url': ('armstrong.apps.embeds.fields.EmbedURLField', [], {'response_field': "'response'", 'max_length': '200', 'unique': 'True', 'assign_func': "'_auto_assign_backend'"})
        },
        'embeds.provider': {
            'Meta': {'object_name': 'Provider'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        'embeds.type': {
            'Meta': {'object_name': 'Type'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '25'})
        }
    }

    complete_apps = ['embeds']