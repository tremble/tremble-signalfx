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

extends_documentation_fragment:
- tremble.signalfx.signalfx
'''

EXAMPLES = '''
# Set the 'project_name' custom property on the 'project_id:{{ project_id }}' dimension.
- dimension:
    key: project_id
    value: '{{ project_id }}'
    properties:
      project_name: '{{ project_name }}'
    realm: us1
    auth_token: 'abc123456789def'

# Remove all custom properties from the 'project_id:{{ project_id }}' dimension.
- dimension:
    key: project_id
    value: '{{ project_id }}'
    properties: {}
    purge_properties: True
    realm: us1
    auth_token: 'abc123456789def'

# Add a tag to the 'project_id:{{ project_id }}' dimension.
- dimension:
    key: project_id
    value: '{{ project_id }}'
    tags:
    - MyExampleTag
    realm: us1
    auth_token: 'abc123456789def'
'''

RETURN = '''
dimension:
  description:
    - A dictionary describing the dimension.
  returned: On success
  type: dict
  contains:
    key:
      description: Dimension name.
      returned: On success
      type: str
      sample: "some_dimension"
    value:
      description: Dimension value.
      returned: On success
      type: str
      sample: "MyValue"
    created:
      description: The time that the dimension was created (Unix time).
      returned: On success
      type: int
      sample: 1612972485414
    creator:
      description: The ID of the user that created the dimension.
      returned: On success
      type: str
      sample: "ABCDEF12345"
    description:
      description: Dimension description (up to 1024 UTF8 characters).
      returned: On success
      type: str
      sample: "My Dimension"
    last_updated:
      description: The time that the dimension was last updated (Unix time).
      returned: On success
      type: int
      sample: 1641302231514
    last_updated_by:
      description: The ID of the user that last updated the dimension.
      returned: On success
      type: str
      sample: "ABCDEF12345"
    tags:
      description: A list of the tags for the dimension.
      returned: On success
      type: list
      elements: str
      sample: ["tag1", "tag2"]
    custom_properties:
      description: A dictionary representing the custom properties for the dimension.
      returned: On success
      type: dict
      sample: {"project_name": "My Project Name"}
'''

from copy import deepcopy

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ..module_utils.core import AnsibleSignalFxModule
from ..module_utils.core import SignalFxRestManager


class SignalFxDimension(SignalFxRestManager):

    def __init__(self, module):
        super().__init__(module)

        self._update_params = dict()

        self.dimension = self._get_dimension() or dict()
        self.original_dimension = deepcopy(self.dimension)

    @SignalFxRestManager.api_error_handler(description="get dimension")
    def _get_dimension(self):
        dimension = self.client.get_dimension(
            key=self.module.params.get('key'),
            value=self.module.params.get('value'),
        )
        return camel_dict_to_snake_dict(dimension, ignore_list=['custom_properties'])

    @SignalFxRestManager.api_error_handler(description="update dimension", ignore_404=False)
    def _update_dimension(self, **kwargs):
        dimension = self.client.update_dimension(
            key=self.module.params.get('key'),
            value=self.module.params.get('value'),
            **kwargs
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
    )

    module = AnsibleSignalFxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

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
