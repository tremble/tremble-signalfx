#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: dimension
version_added: 0.1.0
short_description: manages SignalFX dimension metadata
author:
- Mark Chappell (@tremble)
description:
- Manages SignalFX dimenstion metadata.
options:
  key:
    description:
    - Name of the dimension to update.
    type: str
    required: true
    aliases: ['name']
  value:
    description:
    - Value of the dimension to update.
    type: str
    required: true
  description:
    description:
    - Description of the dimension.
    type: str
  tags:
    description:
    - Tags to add or update for the specified dimension key and value.
    type: list
    elements: str
  purge_tags:
    description:
    - Whether to remove existing tags that aren't passed in the I(tags) parameter.
    default: false
    type: bool
  custom_properties:
    description:
    - Custom properties to add or update for the specified dimension key and value.
    type: dict
    aliases: ['properties']
  purge_properties:
    description:
    - Whether to remove existing properties that aren't passed in the I(properties) parameter.
    default: false
    type: bool
  auth_token:
    description:
    - The SignalFX authentication token.
    type: str
    required: true
  realm:
    description:
    - The SignalFX realm to use.
    default: 'us0'
    type: str
'''

EXAMPLES = '''
'''

RETURN = '''
'''

try:
    import signalfx
    HAS_SIGNALFX = True
except ImportError:
    HAS_SIGNALFX = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict


class SignalFxDimension():

    # XXX Will probably be refactored
    @staticmethod
    def _merge_set(current, new, purge):
        _current = set(current)
        _new = set(new)
        if purge:
            final = _new
        else:
            final = _new | _current

        return final

    @staticmethod
    def _merge_dict(current, new, purge):
        _current = deepcopy(current)
        if purge:
            final = dict()
        else:
            final = _current
        final.update(new)

        return final

    def __init__(self, module):
        realm = module.params.get('realm')
        token = module.params.get('auth_token')

        self.module = module
        self.check_mode = module.check_mode
        self.changed = False
        self._update_params = dict()

        sfx = signalfx.SignalFx(
            api_endpoint='https://api.{REALM}.signalfx.com'.format(REALM=realm),
            ingest_endpoint='https://ingest.{REALM}.signalfx.com'.format(REALM=realm),
            stream_endpoint='https://stream.{REALM}.signalfx.com'.format(REALM=realm),
        )

        self.client = sfx.rest(token)
        self.dimension = self._get_dimension()
        self.original_dimension = deepcopy(self.dimension)

    def _get_dimension(self):
        try:
            dimension = self.client.get_dimension(
                key=self.module.params.get('key'),
                value=self.module.params.get('value'),
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return dict()
            self.module.fail_json(
                msg='Failed to get dimension: {0}'.format(e),
                status_code=e.response.status_code,
            )
        return camel_dict_to_snake_dict(dimension, ignore_list=['custom_properties'])

    def _update_dimension(self, **kwargs):
        try:
            dimension = self.client.update_dimension(
                key=self.module.params.get('key'),
                value=self.module.params.get('value'),
                **kwargs
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return dict()
            self.module.fail_json(
                msg='Failed to update dimension: {0}'.format(e),
                status_code=e.response.status_code,
            )
        return camel_dict_to_snake_dict(dimension, ignore_list=['custom_properties'])

    def set_description(self, description):
        if description is None:
            return
        if description == self.dimension.get('description', None):
            return
        self.dimension['description'] = description
        self._update_params['description'] = description
        self.changed = True
        return

    def set_tags(self, tags, purge_tags):
        if tags is None:
            return
        final_tags = self._merge_set(
            self.dimension.get('tags', []),
            tags, purge_tags,
        )
        if set(final_tags) == set(self.dimension.get('tags', [])):
            return
        self.dimension['tags'] = list(final_tags)
        self._update_params['tags'] = list(final_tags)
        self.changed = True
        return

    def set_properties(self, properties, purge_properties):
        if properties is None:
            return
        final_properties = self._merge_dict(
            self.dimension.get('custom_properties', dict()),
            properties, purge_properties,
        )
        if final_properties == self.dimension.get('custom_properties', dict()):
            return
        self.dimension['custom_properties'] = final_properties
        self._update_params['custom_properties'] = final_properties
        self.changed = True
        return

    def flush_updates(self):
        if not self._update_params:
            return False
        if self.check_mode:
            return True
        self.dimension = self._update_dimension(**self._update_params)
        return True


def main():

    argument_spec = dict(
        key=dict(type='str', required=True, aliases=['name'], no_log=False),
        value=dict(type='str', required=True),
        description=dict(type='str'),
        custom_properties=dict(type='dict', aliases=['properties']),
        tags=dict(type='list', elements='str'),
        purge_properties=dict(type='bool', default=False),
        purge_tags=dict(type='bool', default=False),
        auth_token=dict(type='str', required=True, no_log=True),
        realm=dict(type='str', default='us0'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_SIGNALFX:
        module.fail_json(msg='Failed to import required Python module "signalfx"')
    if not HAS_REQUESTS:
        module.fail_json(msg='Failed to import required Python module "requests"')

    sfx_dimension = SignalFxDimension(module)
    sfx_dimension.set_description(
        module.params.get('description', None),
    )
    sfx_dimension.set_tags(
        module.params.get('tags', None),
        module.params.get('purge_tags'),
    )
    sfx_dimension.set_properties(
        module.params.get('custom_properties', None),
        module.params.get('purge_properties'),
    )
    changed = sfx_dimension.flush_updates()
    diff = dict(
        before=sfx_dimension.original_dimension,
        after=sfx_dimension.dimension,
    )
    results = dict(dimension=sfx_dimension.dimension, diff=diff)

    module.exit_json(changed=changed, **results)


if __name__ == '__main__':
    main()
