from flask import Flask
from flask_cors import CORS

#from http.client import HTTPConnection
import json
#import requests

from datetime import datetime, date

from kafka import KafkaProducer
import decimal
from orm.models import Statuses_AutoCall 

EVENTS_NOT_LISTEN = ['RTCPSent', 'RTCPReceived', 'PeerStatus', 'NewAccountCode']

EVENTS_VARS_LISTEN = ['DIALSTATUS', 'MIXMONITOR_FILENAME', 'TEXT_SP_RES', 'RECORDED_FILE', 'PLAYBACKSTATUS']

USER_EVENTS = {}

AUTO_CALLS = {}


def ami_client_event(jdata, user):
    key = user.encode('utf-8')
    value = jdata.encode('utf-8')
        
    #print(jdata)                    
    
    try:
        producer.send(f'ami_client_event', key=key, value=value)
    except:
        print(f"""send to kafka failed {jdata}""")

    pass

def auto_call_event(jdata):
    key = 'auto_call_set_status'.encode('utf-8')
    value = jdata.encode('utf-8')

    #print(jdata)

    try:
        #producer.send(f'ones_ws_event', key=key, value=value)
        producer.send(f'ones_http_event', key=key, value=value)
    except:
        print(f"""send to kafka failed {jdata}""")

    pass

def do_handle_event(event):
    #print(f"""{str(event)}""")

    if event.name == 'Dial':
        for x in AUTO_CALLS:
            if x in event.keys['Channel']:
                Destination = event.keys.get('Destination')
                
                if Destination is None:
                    continue
                
                AUTO_CALLS[x]['Destination'] = Destination

                d = {}
                
                d['Действия'] = 'Asterisk_AutoCall_Event' 
                d['Данные'] = event.keys 
                d['Данные']['name'] = event.name 
                d['Данные']['id_ext'] = AUTO_CALLS[x]['id_ext']
                d['Данные']['id'] = AUTO_CALLS[x]['id']
                d['Данные']['event_date'] = datetime.now()
                
                jdata = json.dumps(d, default=json_serial)
                
                auto_call_event(jdata)

                #print(f"""{str(event)}""")

    elif event.name == 'DTMF':
        for x in AUTO_CALLS:
            if AUTO_CALLS[x].get('Destination') is None:
                continue

            if AUTO_CALLS[x]['Destination']  in event.keys['Channel']:
                d = {}
                
                d['Действия'] = 'Asterisk_AutoCall_Event' 
                d['Данные'] = event.keys 
                d['Данные']['name'] = event.name 
                d['Данные']['id_ext'] = AUTO_CALLS[x]['id_ext']
                d['Данные']['id'] = AUTO_CALLS[x]['id']
                d['Данные']['event_date'] = datetime.now()
                
                jdata = json.dumps(d, default=json_serial)
                
                auto_call_event(jdata)

                #print(f"""{str(event)}""")


    elif event.name == 'Newstate' or event.name == 'Hangup' or event.name == 'VarSet':
        if event.name == 'VarSet':
            if not event.keys['Variable'] in EVENTS_VARS_LISTEN:
                return

        for x in USER_EVENTS:
            if USER_EVENTS[x].get('channel') is None:
                continue

            if USER_EVENTS[x]['channel'] in event.keys['Channel']:
                d = {}
                
                d['Действия'] = 'Asterisk_Event' 
                d['Данные'] = event.keys 
                d['Данные']['name'] = event.name 
                d['Данные']['id_ext'] = USER_EVENTS[x]['id_ext'] 
                d['Данные']['event_date'] = datetime.now()
                
                jdata = json.dumps(d, default=json_serial)
                
                ami_client_event(jdata, USER_EVENTS[x]['user'])

                #print(f"""{str(event)}""")

        for x in AUTO_CALLS:
            if AUTO_CALLS[x].get('Destination') is None:
                continue
            
            if x in event.keys['Channel'] or AUTO_CALLS[x]['Destination'] in event.keys['Channel']:
                if event.name == 'Hangup':
                     if event.keys['CallerIDNum'] != AUTO_CALLS[x]['callerid']:
                         continue
                d = {}
                
                d['Действия'] = 'Asterisk_AutoCall_Event' 
                d['Данные'] = event.keys 
                d['Данные']['name'] = event.name 
                d['Данные']['id_ext'] = AUTO_CALLS[x]['id_ext']
                d['Данные']['id'] = AUTO_CALLS[x]['id']
                d['Данные']['event_date'] = datetime.now()
                
                jdata = json.dumps(d, default=json_serial)
                
                auto_call_event(jdata)

                #print(f"""{str(event)}""")


def event_listener(event, **kwargs):
    if event.name in EVENTS_NOT_LISTEN:
        return

    try:
        do_handle_event(event)
    except Exception as e:
        print('error')
        print(e)
        print(event)

    pass

def json_serial(obj):
    if isinstance(obj, (datetime, date)):
       return obj.isoformat()

    if isinstance(obj, decimal.Decimal):
       return float(obj)
    pass


app = Flask(__name__)

producer = KafkaProducer(bootstrap_servers=['192.168.5.131:9092'])

CORS(app, support_credentials=True)

import server.views

from asterisk.ami import AMIClient, AMIClientAdapter, AutoReconnect
from server.conf import *

client = AMIClient(address=AMI_ADDRESS, port=AMI_PORT)
AutoReconnect(client)

future = client.login(username=AMI_USER, secret=AMI_SECRET)

client.add_event_listener(event_listener)

