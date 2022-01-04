#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: session
version_added: 0.1.0
short_description: log into the SignalFX API
author:
- Mark Chappell (@tremble)
description:
- Logs into the SignalFX API and generates a session token.
options:
  email:
    description:
    - The email address of the user.
    type: str
    required: true
  password:
    description:
    - The password of the user
    type: str
    required: true
  realm:
    description:
    - The SignalFX realm to use.
    default: 'us0'
    type: str
'''

EXAMPLES = '''
# Login using an email/password
- session:
    realm: us1
    email: somebody@example.com
    password: Not-A-Real-Password
'''

RETURN = '''
token:
  description:
  - A SignalFX Session token.
  type: str
  returned: On success
'''

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.core import SignalFxBaseManager


class SignalFxSession(SignalFxBaseManager):

    def __init__(self, module):
        super().__init__(module)

    @SignalFxBaseManager.api_error_handler(description="login", ignore_404=False)
    def _login(self, **kwargs):
        return self._sfx.login(**kwargs)

    def login(self, email, password):
        return self._login(email=email, password=password)


def main():

    argument_spec = dict(
        email=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        realm=dict(type='str', default='us0'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    sfx_session = SignalFxSession(module)
    token = sfx_session.login(
        module.params.get('email'),
        module.params.get('password')
    )

    module.exit_json(changed=True, token=token)


if __name__ == '__main__':
    main()
