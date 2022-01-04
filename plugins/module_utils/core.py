# -*- coding: utf-8 -*-
#
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright: Ansible Project
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

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
from functools import wraps

from ansible.module_utils.basic import AnsibleModule


class SignalFxBaseManager():

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

        if not HAS_SIGNALFX:
            module.fail_json(msg='Failed to import required Python module "signalfx"')
        if not HAS_REQUESTS:
            module.fail_json(msg='Failed to import required Python module "requests"')

        realm = module.params.get('realm')

        self.module = module
        self.check_mode = module.check_mode
        self.changed = False

        self._sfx = signalfx.SignalFx(
            api_endpoint='https://api.{REALM}.signalfx.com'.format(REALM=realm),
            ingest_endpoint='https://ingest.{REALM}.signalfx.com'.format(REALM=realm),
            stream_endpoint='https://stream.{REALM}.signalfx.com'.format(REALM=realm),
        )

    @staticmethod
    def api_error_handler(description, ignore_404=True):

        def wrapper(func):
            @wraps(func)
            def handler(_self, *args, **kwargs):
                try:
                    return func(_self, *args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    if ignore_404 and e.response.status_code == 404:
                        return None
                    _self.module.fail_json(
                        msg='Failed to {DESC}: {ERR}'.format(DESC=description, ERR=e),
                        status_code=e.response.status_code,
                    )

            return handler

        return wrapper


class SignalFxRestManager(SignalFxBaseManager):

    def __init__(self, module):
        super().__init__(module)

        token = module.params.get('auth_token')
        self.client = self._sfx.rest(token)


class AnsibleSignalFxModule(AnsibleModule):

    def __init__(self, *args, **kwargs):
        argument_spec = dict(
            auth_token=dict(type='str', required=True, no_log=True),
            realm=dict(type='str', default='us0'),
        )
        arg_spec = kwargs.get('argument_spec', dict())
        argument_spec.update(arg_spec)
        kwargs['argument_spec'] = argument_spec
        super().__init__(*args, **kwargs)
