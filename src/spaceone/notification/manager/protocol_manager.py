import logging
from spaceone.core.manager import BaseManager
from spaceone.notification.model.protocol_model import Protocol
from spaceone.notification.conf.protocol_conf import DEFAULT_PROTOCOLS
from pprint import pprint
from spaceone.notification.error import *

_LOGGER = logging.getLogger(__name__)


class ProtocolManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol_model: Protocol = self.locator.get_model('Protocol')

    def create_protocol(self, params):
        def _rollback(protocol_vo):
            _LOGGER.info(f'[create_protocol._rollback]'
                         f'Delete Protocol : {protocol_vo.name}'
                         f'({protocol_vo.protocol_id})')
            protocol_vo.delete()
        pprint(params)
        protocol_vo: Protocol = self.protocol_model.create(params)
        self.transaction.add_rollback(_rollback, protocol_vo)

        return protocol_vo

    def update_protocol(self, params):
        protocol_vo: Protocol = self.get_protocol(params['protocol_id'], params['domain_id'])
        return self.update_protocol_by_vo(params, protocol_vo)

    def update_protocol_by_vo(self, params, protocol_vo):
        def _rollback(old_data):
            _LOGGER.info(f'[update_protocol_by_vo._rollback] Revert Data : '
                         f'{old_data["protocol_id"]}')
            protocol_vo.update(old_data)

        self.transaction.add_rollback(_rollback, protocol_vo.to_dict())
        return protocol_vo.update(params)

    def delete_protocol(self, protocol_id, domain_id):
        protocol_vo: Protocol = self.get_protocol(protocol_id, domain_id)
        # TODO: Required to check existed channel using protocol
        protocol_vo.delete()

    def enable_protocol(self, protocol_id, domain_id):
        def _rollback(old_data):
            _LOGGER.info(f'[enable_protocol._rollback] Revert Data : {old_data["name"]} ({old_data["protocol_id"]})')
            protocol_vo.update(old_data)

        protocol_vo: Protocol = self.get_protocol(protocol_id, domain_id)

        if protocol_vo.state != 'ENABLED':
            self.transaction.add_rollback(_rollback, protocol_vo.to_dict())
            protocol_vo.update({'state': 'ENABLED'})

        return protocol_vo

    def disable_protocol(self, protocol_id, domain_id):
        def _rollback(old_data):
            _LOGGER.info(f'[disable_protocol._rollback] Revert Data : {old_data["name"]} ({old_data["protocol_id"]})')
            protocol_vo.update(old_data)

        protocol_vo: Protocol = self.get_protocol(protocol_id, domain_id)

        if protocol_vo.state != 'DISABLED':
            self.transaction.add_rollback(_rollback, protocol_vo.to_dict())
            protocol_vo.update({'state': 'DISABLED'})

        return protocol_vo

    def get_protocol(self, protocol_id, domain_id, only=None):
        return self.protocol_model.get(protocol_id=protocol_id, domain_id=domain_id, only=only)

    def list_protocols(self, query={}):
        return self.protocol_model.query(**query)

    def stat_protocols(self, query):
        return self.protocol_model.stat(**query)

    def create_default_protocols(self, installed_protocols, domain_id):
        for single_protocol in DEFAULT_PROTOCOLS:
            if single_protocol['name'] not in installed_protocols:
                _LOGGER.debug(f'Create default protocol: {single_protocol["name"]}')
                single_protocol['domain_id'] = domain_id
                self.create_protocol(single_protocol)
