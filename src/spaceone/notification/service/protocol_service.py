import logging
from spaceone.core import cache

from spaceone.core.service import *
from spaceone.notification.error import *
from spaceone.notification.manager import RepositoryManager
from spaceone.notification.manager import ProtocolManager
from spaceone.notification.manager import PluginManager
from spaceone.notification.model import Protocol

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class ProtocolService(BaseService):

    def __init__(self, metadata):
        super().__init__(metadata)
        self.protocol_mgr: ProtocolManager = self.locator.get_manager('ProtocolManager')

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['name', 'plugin_info', 'domain_id'])
    def create(self, params):
        """ Create Protocol

        Args:
            params (dict): {
                'name': 'str',
                'plugin_info': 'dict',
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            protocol_vo (object)
        """
        domain_id = params['domain_id']
        self._check_plugin_info(params['plugin_info'])
        # plugin_info = self._get_plugin(params['plugin_info'], params['domain_id'])

        # TODO::1 Please, Add a real Plugin_info to retrieve when its ready.
        plugin_info = params['plugin_info']
        options = plugin_info.get('options', {})
        params['capability'] = options.get('capability')
        del options['capability']

        self._check_plugin_capability(params['capability'])

        _LOGGER.debug(f'[create] capability: {params["capability"]}')
        _LOGGER.debug(f'[create] name: {params["name"]}')

        params['protocol_type'] = 'EXTERNAL'
        params['resource_type'] = 'inventory.Collector'

        # TODO::2 Please, Add a real Plugin_info to retrieve when its ready.
        # plugin_metadata = self._init_plugin(params['plugin_info'], domain_id)
        # params['plugin_info']['metadata'] = plugin_metadata

        protocol_vo: Protocol = self.protocol_mgr.create_protocol(params)

        return protocol_vo

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['protocol_id', 'domain_id'])
    def update(self, params):
        """ Update protocol

        Args:
            params (dict): {
                'protocol_id': 'str',
                'name': 'str',
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            protocol_vo (object)
        """

        domain_id = params['domain_id']
        protocol_id = params['protocol_id']
        selected_protocol_type_vo = self.protocol_mgr.get_protocol(protocol_id, domain_id, ['protocol_type'])

        if selected_protocol_type_vo.protocol_type == 'INTERNAL':
            raise ERROR_NOT_ALLOWED_UPDATE_PROTOCOL_TYPE(protocol_id=protocol_id)

        return self.protocol_mgr.update_protocol(params)

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['protocol_id', 'domain_id'])
    def update_plugin(self, params):
        """ Update protocol

        Args:
            params (dict): {
                'protocol_id': 'str',
                'name': 'str',
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            protocol_vo (object)
        """

        protocol_id = params['data_source_id']
        domain_id = params['domain_id']
        options = params.get('options')
        version = params.get('version')

        protocol_vo = self.protocol_mgr.get_protocol(protocol_id, domain_id)
        protocol_dict = protocol_vo.to_dict()
        plugin_info = protocol_dict['plugin_info']

        if version:
            # Update plugin_version
            plugin_id = plugin_info['plugin_id']
            repo_mgr = self.locator.get_manager('RepositoryManager')
            repo_mgr.check_plugin_version(plugin_id, version, domain_id)

            plugin_info['version'] = version
            metadata = self._init_plugin(protocol_dict['plugin_info'], domain_id)
            plugin_info['metadata'] = metadata

        if options or options == {}:
            # Overwriting
            plugin_info['options'] = options

        params = {
            'protocol_id': protocol_id,
            'domain_id': domain_id,
            'plugin_info': plugin_info
        }

        _LOGGER.debug(f'[update_plugin] {plugin_info}')
        return self.protocol_mgr.update_protocol_by_vo(params, protocol_vo)

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['protocol_id', 'domain_id'])
    def delete(self, params):
        """ Delete protocol

        Args:
            params (dict): {
                'protocol_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            None
        """
        protocol_id = params['protocol_id']
        domain_id = params['domain_id']

        return self.protocol_mgr.delete_protocol(protocol_id, domain_id)

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['protocol_id', 'domain_id'])
    def enable(self, params):
        """ Enable protocol

        Args:
            params (dict): {
                'protocol_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            protocol_vo (object)
        """

        return self.protocol_mgr.enable_protocol(params['protocol_id'], params['domain_id'])

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['protocol_id', 'domain_id'])
    def disable(self, params):
        """ Disable protocol

        Args:
            params (dict): {
                'protocol_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            protocol_vo (object)
        """

        return self.protocol_mgr.disable_protocol(params['protocol_id'], params['domain_id'])

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['protocol_id', 'domain_id'])
    def get(self, params):
        """ Disable domain

        Args:
            params (dict): {
                'domain_id': 'str',
                'only': 'list'
            }

        Returns:
            domain_vo (object)
        """
        domain_id = params['domain_id']
        self._create_default_protocol(domain_id)
        return self.protocol_mgr.get_protocol(params['protocol_id'], domain_id, params.get('only'))

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['domain_id'])
    @append_query_filter(['protocol_id', 'name', 'state', 'protocol_type', 'domain_id'])
    @change_tag_filter('tags')
    @append_keyword_filter(['protocol_id'])
    def list(self, params):
        """ List protocol

        Args:
            params (dict): {
                'protocol_id': 'str',
                'name': 'str',
                'state': 'str',
                'protocol_type',
                'query': 'dict (spaceone.api.core.v1.Query)',
                'domain_id': 'str'
            }

        Returns:
            results (list): 'list of protocol_vo'
            total_count (int)
        """
        domain_id = params['domain_id']
        self._create_default_protocol(domain_id)
        query = params.get('query', {})
        return self.protocol_mgr.list_protocols(query)

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['query', 'domain_id'])
    @append_query_filter(['domain_id'])
    @change_tag_filter('tags')
    @append_keyword_filter(['protocol_id', 'name'])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)'
            }

        Returns:
            values (list): 'list of statistics data'
            total_count (int)
        """

        query = params.get('query', {})
        return self.protocol_mgr.stat_protocols(query)

    def _get_plugin(self, plugin_info, domain_id):
        plugin_id = plugin_info['plugin_id']
        version = plugin_info['version']

        repo_mgr: RepositoryManager = self.locator.get_manager('RepositoryManager')
        plugin_info = repo_mgr.get_plugin(plugin_id, domain_id)
        repo_mgr.check_plugin_version(plugin_id, version, domain_id)

        return plugin_info

    def _init_plugin(self, plugin_info, domain_id):
        plugin_id = plugin_info['plugin_id']
        version = plugin_info['version']
        options = plugin_info['options']

        plugin_mgr: PluginManager = self.locator.get_manager('PluginManager')
        plugin_mgr.initialize(plugin_id, version, domain_id)
        endpoint = plugin_mgr.get_endpoint(plugin_id, version, domain_id)

        return plugin_mgr.init_plugin(endpoint, options)

    @staticmethod
    def _check_plugin_capability(capability):
        if 'data_type' not in capability:
            raise ERROR_WRONG_PLUGIN_SETTINGS(key='capability.data_type')
        else:
            if capability['data_type'] not in ['PLAIN_TEXT', 'SECRET']:
                raise ERROR_WRONG_PLUGIN_SETTINGS(key='capability.data_type')

        if 'supported_schema' not in capability:
            raise ERROR_WRONG_PLUGIN_SETTINGS(key='capability.supported_schema')

    @staticmethod
    def _check_plugin_info(plugin_info_params):
        if 'plugin_id' not in plugin_info_params:
            raise ERROR_REQUIRED_PARAMETER(key='plugin_info.plugin_id')
        else:
            temp_plugin_id = plugin_info_params['plugin_id']
            _temp_plugin_id = temp_plugin_id.split('-')
            if len(_temp_plugin_id) != 2:
                raise ERROR_INVALID_PARAMETER(key='plugin_info.plugin_id', reason='wrong format')
            elif _temp_plugin_id[0] != 'plugin':
                raise ERROR_INVALID_PARAMETER(key='plugin_info.plugin_id', reason='wrong format')
            elif len(_temp_plugin_id[1]) != 12:
                raise ERROR_INVALID_PARAMETER(key='plugin_info.plugin_id', reason='wrong format')

        if 'version' not in plugin_info_params:
            raise ERROR_REQUIRED_PARAMETER(key='plugin_info.version')

        if 'options' not in plugin_info_params:
            raise ERROR_REQUIRED_PARAMETER(key='plugin_info.options')

    @cache.cacheable(key='default-protocol:{domain_id}', expire=300)
    def _create_default_protocol(self, domain_id):
        query = {'domain_id': domain_id}
        protocol_vos, total_count = self.protocol_mgr.list_protocols(query)
        installed_protocols = [protocol_vo.name for protocol_vo in protocol_vos]
        self.protocol_mgr.create_default_protocols(installed_protocols, domain_id)
        return True
