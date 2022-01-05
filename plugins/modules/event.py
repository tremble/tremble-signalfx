#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: event
version_added: 0.1.0
short_description: sends SignalFX events
author:
- Mark Chappell (@tremble)
description:
- Sends SignalFX events.
options:
  dimensions:
    description:
    - Dimensions for the event.
    type: dict
  properties:
    description:
    - Properties for the event.
    type: dict
  category:
    description:
    - A category that describes the event.
    type: str
    default: 'USER_DEFINED'
    choices:
    - 'USER_DEFINED'
    - 'ALERT'
    - 'AUDIT'
    - 'JOB'
    - 'COLLECTD'
    - 'SERVICE_DISCOVERY'
    - 'EXCEPTION'
  event_type:
    description:
    - A name for the event.
    aliases: ['name']
    type: str
    required: true
  timestamp:
    description:
    - The time at which the event happened (UNIX time).
    type: int

extends_documentation_fragment:
- tremble.signalfx.signalfx
'''

EXAMPLES = '''
# Send a simple "ExampleTestEvent" event with no metadata
- event:
    event_type: ExampleTestEvent
    realm: us1
    auth_token: "ABCDE12345"

# Send an event with dimenstions attached
- event:
    event_type: ExampleTestEvent
    dimensions:
      application_code: SMPL-001
      hostname: "{{ ansible_fqdn }}"
    realm: us1
    auth_token: "ABCDE12345"
'''

RETURN = '''
event:
  description:
    - A dictionary describing the event sent.
  returned: On success
  type: dict
  contains:
    dimensions:
      description: A dictionary representing the dimensions for the event.
      returned: When dimensions were set.
      type: dict
      sample: {"project_id": "123456789"}
    custom_properties:
      description: A dictionary representing the custom properties for the event.
      returned: When custom properties were set.
      type: dict
      sample: {"project_name": "My Project Name"}
    category:
      description: A category that describes the event.
      returned: On success
      type: str
      sample: "USER_DEFINED"
    event_type:
      description: A name for the event.
      returned: On success
      type: str
      sample: "ExampleTestEvent"
    timestamp:
      description: The time at which the event happened (UNIX time).
      returned: When a timestamp was explicitly sent.
      type: int
      sample: 1641304973451
'''

from ..module_utils.core import AnsibleSignalFxModule
from ..module_utils.core import SignalFxIngestManager


class SignalFxEvent(SignalFxIngestManager):

    def __init__(self, module):
        super().__init__(module)

    @SignalFxIngestManager.api_error_handler(description="send event", ignore_404=False)
    def _send_event(self, **kwargs):
        if self.check_mode:
            return kwargs
        # The API returns no data.  See also:
        # https://dev.splunk.com/observability/reference/api/ingest_data/latest#endpoint-send-events
        self.client.send_event(**kwargs)
        return kwargs

    def send_event(self, event_type, category, dimensions, properties, timestamp):

        event_args = dict(
            event_type=event_type,
            category=category,
        )
        if dimensions:
            event_args['dimensions'] = dimensions
        if properties:
            event_args['properties'] = properties
        if timestamp:
            event_args['timestamp'] = timestamp

        return self._send_event(**event_args)


def main():

    categories = [
        'USER_DEFINED', 'ALERT', 'AUDIT', 'JOB', 'COLLECTD',
        'SERVICE_DISCOVERY', 'EXCEPTION',
    ]

    argument_spec = dict(
        event_type=dict(type='str', required=True, aliases=['name']),
        category=dict(type='str', default='USER_DEFINED', choices=categories),
        dimensions=dict(type='dict'),
        properties=dict(type='dict'),
        timestamp=dict(type='int'),
    )

    module = AnsibleSignalFxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    sfx_event = SignalFxEvent(module)
    event = sfx_event.send_event(
        module.params.get('event_type'),
        module.params.get('category'),
        module.params.get('dimensions', None),
        module.params.get('properties', None),
        module.params.get('timestamp', None),
    )

    module.exit_json(changed=True, event=event)


if __name__ == '__main__':
    main()
