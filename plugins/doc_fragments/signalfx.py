# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):

    # SignalFX Common documentation fragment
    DOCUMENTATION = r'''
options:
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
requirements:
- python >= 3.6
- signalfx
- requests
'''
