# encoding: utf-8
import datetime

from south.db import db
from south.v2 import SchemaMigration

from django.conf import settings
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'StoredOEmbed'
        db.create_table('oembed_storedoembed', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('match', self.gf('django.db.models.fields.TextField')()),
            ('response_json', self.gf('django.db.models.fields.TextField')()),
            ('resource_type', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('date_expires', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('maxwidth', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('maxheight', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('object_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='related_storedoembed', null=True, to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('oembed', ['StoredOEmbed'])

        # Adding unique constraint on 'StoredOEmbed', fields ['match', 'maxwidth', 'maxheight']
        if 'mysql' not in settings.DATABASES['default']['ENGINE']:
            db.create_unique('oembed_storedoembed', ['match', 'maxwidth', 'maxheight'])

        # Adding model 'StoredProvider'
        db.create_table('oembed_storedprovider', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('endpoint_url', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('regex', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('wildcard_regex', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('resource_type', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('provides', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('scheme_url', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('oembed', ['StoredProvider'])

        # Adding model 'AggregateMedia'
        db.create_table('oembed_aggregatemedia', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.TextField')()),
            ('object_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='aggregate_media', null=True, to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('oembed', ['AggregateMedia'])


    def backwards(self, orm):
        
        # Deleting model 'StoredOEmbed'
        db.delete_table('oembed_storedoembed')

        # Removing unique constraint on 'StoredOEmbed', fields ['match', 'maxwidth', 'maxheight']
        if 'mysql' not in settings.DATABASES['default']['ENGINE']:
            db.delete_unique('oembed_storedoembed', ['match', 'maxwidth', 'maxheight'])

        # Deleting model 'StoredProvider'
        db.delete_table('oembed_storedprovider')

        # Deleting model 'AggregateMedia'
        db.delete_table('oembed_aggregatemedia')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'oembed.aggregatemedia': {
            'Meta': {'object_name': 'AggregateMedia'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'aggregate_media'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        'oembed.storedoembed': {
            'Meta': {'ordering': "('-date_added',)", 'unique_together': "(('match', 'maxwidth', 'maxheight'),)", 'object_name': 'StoredOEmbed'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'related_storedoembed'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_expires': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'match': ('django.db.models.fields.TextField', [], {}),
            'maxheight': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'maxwidth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'resource_type': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'response_json': ('django.db.models.fields.TextField', [], {})
        },
        'oembed.storedprovider': {
            'Meta': {'ordering': "('endpoint_url', 'resource_type', 'wildcard_regex')", 'object_name': 'StoredProvider'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'endpoint_url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provides': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'regex': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'resource_type': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'scheme_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'wildcard_regex': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        }
    }

    complete_apps = ['oembed']
