#from common.orm import models as orm
#from common.orm import fields as orm_fields
#import peewee
import datetime
#from common import ones as ones
from common import common
#from playhouse.shortcuts import case
import os
import time
from asterisk.ami import AMIClient, AMIClientAdapter
import socket
import re
from common.conf import * 


d = {'channel':'', 'channel2':'', 'DTMF':'', 'status':'', 'log':''}


#region interfaces_func

def make_call_auto(param):
    tel = kwargs_get(param, 'tel')
    file = kwargs_get(param, 'file')
    
    client = AMIClient(address=AMI_ADDRESS, port=AMI_PORT)
    future = client.login(username=AMI_USER, secret=AMI_SECRET)

    if future.response.is_error():
        raise Exception(str(future.response))

    adapter = AMIClientAdapter(client)

    channel = f'Local/{tel}@ng_ext_autodial'
    d['channel'] = channel

    action_id = tel

    variable = FILE_NAMES[file]

    client.add_event_listener(event_listener)

    #res_call = simple_call_without_oper(channel, data)
    res_call = simple_call_without_oper(adapter, channel, DATA, APP, action_id, variable, tel)

    while True:
        if d['status']=='Error':
            break
        elif d['status']=='ANSWER':
            break
        elif d['status']=='BUSY':
            break
        elif d['status']=='Success':
            break
        if not res_call.response is None:
            d['status'] = res_call.response.status
        time.sleep(0.2)

    client.logoff()

    #print(d['DTMF'])
    #print(d['status'])

    return d

#endregion

#region internal_func_bp

def simple_call_with_oper(channel, exten, caller_id, caller_id_name, action_id, timeout='', context='ng_ext_autodial', priority=1):
    res = adapter.Originate(Channel=channel, Context=context, Exten=exten, ActionID=action_id, Priority=priority,  CallerID=caller_id, CallerIDName=caller_id_name, Timeout=timeout, _callback=callback_response)

    return res

def simple_call_without_oper(adapter, channel, data, app, action_id, variable = '', exten='', timeout='45000', context='ng_ext_autodial'):
    res = adapter.Originate(Channel=channel, Context=context, Application=app, Exten=exten, ActionID=action_id,  Data=data, Timeout=timeout, _callback=callback_response, Variable=variable)

    return res

def callback_response(response):
    if response.status=='Error':
        d['status'] = 'Error'

    return None

def event_listener(event,**kwargs):
    #print('"%s" "%s" \n \r' % (event.name, str(event)))
    if 'DTMF' in event.name:
        if d['channel2'] in event.keys['Channel']:
            d['DTMF'] = event.keys['Digit']
            d['log'] += str(event)

    if not event.keys.get('Channel') is None:
        if d['channel'] in event.keys['Channel']:
            d['log'] += str(event)
            if 'Dial' in event.name:
                d['channel2'] = event.keys['Destination']
            elif 'VarSet' in event.name:
                if event.keys['Variable']=='DIALSTATUS':
                    d['status'] = event.keys['Value']

    return None

#endregion

def kwargs_get(qs, key, default=None):
    res, *junk = qs.get(key, (default,))
    if default is None and res is default:
        raise KeyError(key)
    return res

