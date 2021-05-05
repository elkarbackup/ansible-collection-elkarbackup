#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Eneko Lacunza <elacunza@binovo.es>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: elkarbackup_client

short_description: Manage clients in an Elkarbackup server through REST API.

version_added: "0.1.0"

description: Manage clients in an Elkarbackup server through REST API.

options:
    api_password:
        description: Password for API user.
        required: true
        type: string
    api_url:
        description: API URL without '/api' part, i.e. http://localhost:8000 .
        required: true
        type: string
    api_user:
        description: User for API authentication. This is a regular ADMIN user as of 2.1.x .
        required: true
        type: string
    description:
        description: Client description.
        default: ''
        type: string
    is_active:
        description: Client activation status.
        default: True
        type: bool
    max_parallel_jobs:
        description: Number of parallel jobs allowed for this client.
        default: 1
        type: int
    name:
        description: Name for client.
        required: true
        type: str
    post_scripts:
        description: Postscript ids active for this client.
        default: []
        type: list of int
    pre_scripts:
        description: Postscript ids active for this client.
        default: []
        type: list of int
    quota:
        description: Client quota in KB .
        default: -1
        type: int
    rsync_long_args:
        description: Additional arguments for rsync, long form. Separate multiple args with a space.
        default: ''
        type: str
    rsync_short_args:
        description: Additional arguments for rsync, short form. Separate multiple args with a space.
        default: ''
        type: str
    ssh_args:
        description: Additional arguments for ssh. Separate multiple args with a space.
        default: ''
        type: str
    state:
        description: Desired state for client; present or absent.
        required: true
        type: string
        choices: [ present, absent ]
    url:
        description: Access URL for client, as per Elkarbackup details.
        default: ''
        type: str
        
author:
    - Eneko Lacunza - Binovo IT Human Project SL (@elacunza)
'''

EXAMPLES = r'''
# Create a client
- name: Creation example
  hosts: localhost
  tasks:
  - name: Create Name1 if doesn't exist, otherwise update if necessary
    elkarbackup_client:
      api_url: 'http://localhost:8000'
      api_user: 'root'
      api_password: 'root'
      name: 'Name1'
      description: "Description for Name1
      is_active: False
      quota: 20000
      max_parallel_jobs: 4
      ssh_args: '-P 1000'
      rsync_short_args: '-fGE'
      rsync_long_args: '--longarg'
      pre_scripts: [ 1, 2 ]
      post_scripts: [ 2 ]
      state: present
      url: 'name1.example.com'

# Remove a client
- name: Removal example
  hosts: localhost
  tasks:
  - name: Remove Name1 if exists
    elkarbackup_client:
      api_url: 'http://localhost:8000'
      api_user: 'root'
      api_password: 'root'
      name: 'Name1'
      state: absent
'''

RETURN = r'''
id:
    description: Created or updated client ID.
    type: int
    returned: when state==present and client has been created or updated
    sample: 1
api_result:
    description: The result given by the API.
    type: dict
    contains:
        title:
            description: Title for the error.
            type: str
        detail:
            description: Details about the problem.
            type: str
    returned: only if error happened on API's end
    sample: {"detail": "Script \"1\" is not a client pre script", "title": "An error occurred"}
'''

from ansible.module_utils.basic import AnsibleModule
import requests
from requests.auth import HTTPBasicAuth

__metaclass__ = type



def create_client(api_url, api_user, api_password, client):
    response = requests.post(api_url + "/api/clients.json", auth=HTTPBasicAuth(api_user, api_password), json=client)
    new_client = response.json()
    if 'id' in new_client:
        return int(new_client['id'])
    else:
        return response


def delete_client(api_url, api_user, api_password, id):
    response = requests.delete(api_url + "/api/clients/"+str(id)+".json", auth=HTTPBasicAuth(api_user, api_password))
    if response:
        return True
    else:
        return response 


def get_client_by_name(api_url, api_user, api_password, name):
    query = { 'name': name }
    response = requests.get(api_url + "/api/clients.json", auth=HTTPBasicAuth(api_user, api_password), params=query)
    clients = response.json()
    if len(clients) == 1:
        return clients[0]
    elif len(clients) > 0:
        for c in clients:
            if c['name'] == name:
                return c
        return None 
    else:
        return None


def run_module():
    module_args = dict(
        api_password=dict(type='str', required=True, no_log=True),
        api_url=dict(type='str', required=True),
        api_user=dict(type='str', required=True),
        description=dict(type='str', required=False, default=''),
        is_active=dict(type='bool', required=False, default=True),
        max_parallel_jobs=dict(type='int', required=False, default=1),
        name=dict(type='str', required=True),
        post_scripts=dict(type='list', elements='int', required=False, default=[]),
        pre_scripts=dict(type='list', elements='int', required=False, default=[]),
        quota=dict(type='int', required=False, default=-1),
        rsync_long_args=dict(type='str', required=False, default=''),
        rsync_short_args=dict(type='str', required=False, default=''),
        ssh_args=dict(type='str', required=False, default=''),
        state=dict(type='str', required=True, choices=['present', 'absent']),
        url=dict(type='str', required=False, default='')
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    api_url = module.params['api_url']
    api_user = module.params['api_user']
    api_password = module.params['api_password']
    if module.params['state'] == 'present':
        client = get_client_by_name(api_url, api_user, api_password, module.params['name'])
        if not client is None:
            changed = False
            client['quota'] = int(client['quota'])
            if client['description'] != module.params['description']:
                client['description'] = module.params['description']
                changed = True
            if client['isActive'] != module.params['is_active']:
                client['isActive'] = module.params['is_active']
                changed = True
            if client['maxParallelJobs'] != module.params['max_parallel_jobs']:
                client['maxParallelJobs'] = module.params['max_parallel_jobs']
                changed = True
            if client['name'] != module.params['name']:
                client['name'] = module.params['name']
                changed = True
            if set(client['postScripts']) != set(module.params['post_scripts']):
                client['postScripts'] = module.params['post_scripts']
                changed = True
            if set(client['preScripts']) != set(module.params['pre_scripts']):
                client['preScripts'] = module.params['pre_scripts']
                changed = True
            if client['quota'] != module.params['quota']:
                client['quota'] = module.params['quota']
                changed = True
            if client['rsyncLongArgs'] != module.params['rsync_long_args']:
                client['rsyncLongArgs'] = module.params['rsync_long_args']
                changed = True
            if client['rsyncShortArgs'] != module.params['rsync_short_args']:
                client['rsyncShortArgs'] = module.params['rsync_short_args']
                changed = True
            if client['sshArgs'] != module.params['ssh_args']:
                client['sshArgs'] = module.params['ssh_args']
                changed = True
            if client['url'] != module.params['url']:
                client['url'] = module.params['url']
                changed = True
            if changed:
                id = update_client(api_url, api_user, api_password, client)
                if type(id) is int and id != 0:
                    result['changed'] = True
                    result['id'] = id
                else:
                    result['changed'] = False
                    result['api_result'] = id.json()
                    module.fail_json(msg='Client update failed', **result)
            else:
                result['changed'] = False
        else:
            client = {
                'description': module.params['description'],
                'isActive': module.params['is_active'],
                'maxParallelJobs': module.params['max_parallel_jobs'],
                'name': module.params['name'],
                'preScripts': module.params['pre_scripts'],
                'postScripts': module.params['post_scripts'],
                'quota': module.params['quota'],
                'rsyncLongArgs': module.params['rsync_long_args'],
                'rsyncShortArgs': module.params['rsync_short_args'],
                'sshArgs': module.params['ssh_args'],
                'url': module.params['url']
            }
            id = create_client(api_url, api_user, api_password, client)
            if type(id) is int and id != 0:
                result['changed'] = True
                result['id'] = id
            else:
                result['changed'] = False
                result['api_result'] = id
                module.fail_json(msg='Client creation failed', **result)
    elif module.params['state'] == 'absent':
        client = get_client_by_name(api_url, api_user, api_password, module.params['name'])
        if not client is None:
            ok = delete_client(api_url, api_user, api_password, client['id'])
            if type(ok) is bool and ok:
                result['changed'] = True
            else:
                result['changed'] = False
                result['api_result'] = ok 
                module.fail_json(msg='Client deletion failed', **result)
        else:
            result['changed'] = False
        
    module.exit_json(**result)


def update_client(api_url, api_user, api_password, client):
    id = client['id']
    response = requests.put(api_url + "/api/clients/"+str(id)+".json", auth=HTTPBasicAuth(api_user, api_password), json=client)
    new_client = response.json()
    if 'id' in new_client:
        return new_client['id']
    else:
        return response


def main():
    run_module()


if __name__ == '__main__':
    main()

