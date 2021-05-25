from mongoengine import *
from datetime import datetime
from spaceone.core.error import *
from spaceone.core.model.mongo_model import MongoModel


class PluginInfo(EmbeddedDocument):
    plugin_id = StringField(max_length=40)
    version = StringField(max_length=255)
    options = DictField(default=None)
    metadata = DictField(default=None)
    # secret_id = StringField(max_length=40, null=True)
    # auto_upgrade = BooleanField(default=True)

class Protocol(MongoModel):
    protocol_id = StringField(max_length=40, generate_id='protocol', unique=True)
    name = StringField(max_length=255)
    state = StringField(max_length=20, default='ENABLED')
    protocol_type = StringField(max_length=40, default='EXTERNAL')
    resource_type = StringField(max_length=40, default='identity.User')
    capability = DictField()
    plugin_info = EmbeddedDocumentField(PluginInfo, default=None, null=True)
    tags = DictField()
    domain_id = StringField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)

    meta = {
        'updatable_fields': [
            'name',
            'state',
            'plugin_info',
            'tags'
        ],
        'minimal_fields': [
            'protocol_id',
            'name',
            'state',
        ],
        'ordering': ['name'],
        'indexes': [
            'protocol_id',
            'state',
            'tags'
        ]
    }
