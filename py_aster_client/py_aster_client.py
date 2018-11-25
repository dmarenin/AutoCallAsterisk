import os
import time
from asterisk.ami import AMIClient, AMIClientAdapter
import socket
import re

AMI_SECRET = '' 
AMI_USER = ''
AMI_PORT = 5038 
AMI_ADDRESS = '' 


client = AMIClient(address=AMI_ADDRESS, port=AMI_PORT)
future = client.login(username=AMI_USER, secret=AMI_SECRET)

if future.response.is_error():
    raise Exception(str(future.response))

adapter = AMIClientAdapter(client)

def simple_call_with_oper(channel, exten, caller_id, caller_id_name, action_id, timeout='', context='local', priority=1):
    res = adapter.Originate(Channel=channel, Exten=exten, ActionID=action_id, Priority=priority, Context=context, CallerID=caller_id, CallerIDName=caller_id_name, Timeout=timeout)

    return res

def simple_call_without_oper(channel, data, app, action_id, timeout='300000', context='local'):
    res = adapter.Originate(Channel=channel, Application=app, ActionID=action_id, Context=context, Data=data, Timeout=timeout, _callback=callback_response)

    return res

def callback_response(response):
    print(response)

def event_listener(event,**kwargs):
    if event.name=="""DTMF""":
        print('"%s" "%s" \n \r' % (event.name, str(event)))

channel = 'SIP/7099'
exten = '89329999999'
caller_id = 'позвонить сереже'
caller_id_name = 'позвонить сереже'
res_call = simple_call_with_oper(channel, exten, caller_id, caller_id_name)

channel = f'SIP/{exten}@ng_ext'
app = 'Read'
#app = 'BackGround'
action_id = ''
var1 = ''
data = 'var1,/usr/local/share/asterisk/.../.../.../generate,1'

res_call = simple_call_without_oper(channel, data, app, action_id)

client.add_event_listener(event_listener)

try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    client.logoff()

