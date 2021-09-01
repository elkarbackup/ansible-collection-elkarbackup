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
module: elkarbackup_job

short_description: Manage jobs in an Elkarbackup server through REST API.

version_added: "0.1"

description: Manage jobs in an Elkarbackup server through REST API.

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
    backup_location:
        description: Backup location ID.
        default: 1
        type: int
    client_name:
        description: Job will be created/updated/removed from the client with this name.
        required: true
        type: string
    description:
        description: Job description.
        default: ''
        type: string
    exclude:
        description: Exclude pattern.
        default: null
        type: string
    include:
        description: Include pattern.
        default: null
        type: string
    is_active:
        description: Job activation status.
        default: True
        type: bool
    min_notification_level:
        description: Email notification level
        default: 0
        type: int
    name:
        description: Name for job.
        required: true
        type: str
    notifications_email:
        description: Email destination for notifications
        default: null
        type: str
    notifications_to:
        description: Notification email recipients
        type: list
        elements: string
        choices: [ admin, owner, email ]
    path:
        description: Base path for backup
        type: string
        required: True
    policy:
        description: Policy ID.
        default: 1
        type: int
    post_scripts:
        description: Postscript IDs active for this job.
        default: []
        type: list of int
    pre_scripts:
        description: Postscript IDs active for this job.
        default: []
        type: list of int
    token:
        description: Token for enqueuing job externally.
        default: ''
        type: string
    use_local_permissions:
        description: Enable local permissions on backup
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
  - name: Create job job1 for client Name1 if doesn't exist, otherwise update if necessary
    elkarbackup_job:
      api_url: 'http://localhost:8000'
      api_user: 'root'
      api_password: 'root'
      name: 'job1'
      client_name: 'Name1'
      path: '/backup'
      is_active: False
      description: 'Test description for job1'
      notifications_to: [ 'admin', 'owner', 'email']
      notifications_email: 'testjob@example.com'
      min_notification_level: 0
      pre_scripts: [ 1  ]
      post_scripts: [ 1, 2 ]
      state: present
      policy: 1
      use_local_permissions: True
      include: 'includetext'
      exclude: 'excludetext'
      backup_location: 1
      token: 'testoken'

# Remove a client
- name: Removal example
  hosts: localhost
  tasks:
  - name: Remove job1 if exists
    elkarbackup_job:
      api_url: 'http://localhost:8000'
      api_user: 'root'
      api_password: 'root'
      name: 'job1'
      state: absent
'''

RETURN = r'''
id:
    description: Created or updated job ID.
    type: int
    returned: when state==present and job has been created or updated
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
    sample: {"detail": "Script \"1\" is not a job pre script", "title": "An error occurred"}
'''

from ansible.module_utils.basic import AnsibleModule
import requests
from requests.auth import HTTPBasicAuth

__metaclass__ = type


def create_job(api_url, api_user, api_password, job):
    response = requests.post(api_url + "/api/jobs.json", auth=HTTPBasicAuth(api_user, api_password), json=job)
    new_job = response.json()
    if 'id' in new_job:
        return int(new_job['id'])
    else:
        return response


def delete_job(api_url, api_user, api_password, id):
    response = requests.delete(api_url + "/api/jobs/"+str(id)+".json", auth=HTTPBasicAuth(api_user, api_password))
    if response:
        return True
    else:
        return response


def get_client_by_name(api_url, api_user, api_password, name):
    query = {'name': name}
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


def get_job_by_name(api_url, api_user, api_password, name):
    query = {'name': name}
    response = requests.get(api_url + "/api/jobs.json", auth=HTTPBasicAuth(api_user, api_password), params=query)
    jobs = response.json()
    if len(jobs) == 1:
        return jobs[0]
    elif len(jobs) > 0:
        for j in jobs:
            if j['name'] == name:
                return j
        return None
    else:
        return None


def run_module():
    module_args = dict(
        api_password=dict(type='str', required=True, no_log=True),
        api_url=dict(type='str', required=True),
        api_user=dict(type='str', required=True),
        backup_location=dict(type='int', required=False, default=1),
        client_name=dict(type='str', default=''),
        description=dict(type='str', required=False, default=''),
        exclude=dict(type='str', required=False, default=None),
        include=dict(type='str', required=False, default=None),
        is_active=dict(type='bool', required=False, default=True),
        min_notification_level=dict(type='int', required=False, default=0),
        name=dict(type='str', required=True),
        notifications_email=dict(type='str', required=False, default=None),
        notifications_to=dict(type='list', elements='str', required=False, default=''),
        path=dict(type='str', default=''),
        policy=dict(type='int', required=False, default=1),
        post_scripts=dict(type='list', elements='int', required=False, default=[]),
        pre_scripts=dict(type='list', elements='int', required=False, default=[]),
        token=dict(type='str', required=False, default=''),
        state=dict(type='str', required=True, choices=['present', 'absent']),
        use_local_permissions=dict(type='bool', required=False, default=True)
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
        client = get_client_by_name(api_url, api_user, api_password, module.params['client_name'])
        if client is None:
            result['changed'] = False
            result['api_result'] = dict(title='Client name not found', detail='Client name '+module.params['client_name']+' not found')
            module.fail_json(msg='Play failed', **result)
        job = get_job_by_name(api_url, api_user, api_password, module.params['name'])
        if job is not None:
            changed = False
            if job['backupLocation'] != module.params['backup_location']:
                job['backupLocation'] = module.params['backup_location']
                changed = True
            if job['client'] != client['id']:
                job['client'] = client['id']
                changed = True
            if job['description'] != module.params['description']:
                job['description'] = module.params['description']
                changed = True
            if job['exclude'] != module.params['exclude']:
                job['exclude'] = module.params['exclude']
                changed = True
            if job['include'] != module.params['include']:
                job['include'] = module.params['include']
                changed = True
            if job['isActive'] != module.params['is_active']:
                job['isActive'] = module.params['is_active']
                changed = True
            if job['minNotificationLevel'] != module.params['min_notification_level']:
                job['minNotificationLevel'] = module.params['min_notification_level']
                changed = True
            if job['name'] != module.params['name']:
                job['name'] = module.params['name']
                changed = True
            if job['notificationsEmail'] != module.params['notifications_email']:
                job['notificationsEmail'] = module.params['notifications_email']
                changed = True
            if set(job['notificationsTo']) != set(module.params['notifications_to']):
                job['notificationsTo'] = module.params['notifications_to']
                changed = True
            if job['path'] != module.params['path']:
                job['path'] = module.params['path']
                changed = True
            if job['policy'] != module.params['policy']:
                job['policy'] = module.params['policy']
                changed = True
            if set(job['postScripts']) != set(module.params['post_scripts']):
                job['postScripts'] = module.params['post_scripts']
                changed = True
            if set(job['preScripts']) != set(module.params['pre_scripts']):
                job['preScripts'] = module.params['pre_scripts']
                changed = True
            if job['token'] != module.params['token']:
                job['token'] = module.params['token']
                changed = True
            if job['useLocalPermissions'] != module.params['use_local_permissions']:
                job['useLocalPermissions'] = module.params['use_local_permissions']
                changed = True
            if changed:
                id = update_job(api_url, api_user, api_password, job)
                if type(id) is int and id != 0:
                    result['changed'] = True
                    result['id'] = id
                else:
                    result['changed'] = False
                    result['api_result'] = id.json()
                    module.fail_json(msg='Job update failed', **result)
            else:
                result['changed'] = False
        else:
            job = {
                'backupLocation': module.params['backup_location'],
                'client': client['id'],
                'description': module.params['description'],
                'exclude': module.params['exclude'],
                'include': module.params['include'],
                'isActive': module.params['is_active'],
                'minNotificationLevel': module.params['min_notification_level'],
                'name': module.params['name'],
                'notificationsEmail': module.params['notifications_email'],
                'notificationsTo': module.params['notifications_to'],
                'path': module.params['path'],
                'policy': module.params['policy'],
                'postScripts': module.params['post_scripts'],
                'preScripts': module.params['pre_scripts'],
                'token': module.params['token'],
                'useLocalPermissions': module.params['use_local_permissions'],
            }
            id = create_job(api_url, api_user, api_password, job)
            if type(id) is int and id != 0:
                result['changed'] = True
                result['id'] = id
            else:
                result['changed'] = False
                result['api_result'] = id.json()
                module.fail_json(msg='Job creation failed', **result)
    elif module.params['state'] == 'absent':
        job = get_job_by_name(api_url, api_user, api_password, module.params['name'])
        if job is not None:
            ok = delete_job(api_url, api_user, api_password, job['id'])
            if type(ok) is bool and ok:
                result['changed'] = True
            else:
                result['changed'] = False
                result['api_result'] = ok
                module.fail_json(msg='Job deletion failed', **result)
        else:
            result['changed'] = False

    module.exit_json(**result)


def update_job(api_url, api_user, api_password, job):
    id = job['id']
    response = requests.put(api_url + "/api/jobs/"+str(id)+".json", auth=HTTPBasicAuth(api_user, api_password), json=job)
    new_job = response.json()
    if 'id' in new_job:
        return new_job['id']
    else:
        return response


def main():
    run_module()


if __name__ == '__main__':
    main()
