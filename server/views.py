from datetime import datetime, date, timedelta
from flask import render_template, request
from server import app, USER_EVENTS, AUTO_CALLS, auto_call_event
import json
import decimal
from asterisk.ami import AMIClient, AMIClientAdapter
import time
from server.conf import *
import uuid
import requests
import xmltodict
from orm.models import Statuses_AutoCall 


HEADERS = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST", "Access-Control-Allow-Headers": "Content-Type"}
TOKEN = "TOKEN"

ANSWERS_POSITIVE = ['да', 'приеду', 'согласен', 'соглаcна']
ANSWERS_NEGATIVE = ['нет', 'не приеду']
ANSWERS_RE_RECORD = ['перезапишите', 'перезаписать', 'перезапись']


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/make_call')
def make_call():
    client = AMIClient(address=AMI_ADDRESS, port=AMI_PORT)
    future = client.login(username=AMI_USER, secret=AMI_SECRET)
    
    id = request.args.get('id', '')
    channel = request.args.get('channel', '')
    exten = request.args.get('exten', '')
    caller_id = request.args.get('caller_id', '')
    caller_id_name = request.args.get('caller_id_name', '')
    user = request.args.get('user', '')
    action_id = request.args.get('action_id', '')
    
    d = {}
    
    exten = '8' + exten

    id_ext = uuid.uuid4()
    id_ext = str(id_ext)
    
    if future.response.is_error():
        d['status'] = 'failed'
        d['error'] = str(future.response)
        res = json.dumps(d, default=json_serial)
        
        return res, 200, HEADERS

    adapter = AMIClientAdapter(client)

    res_call = do_call_with_oper(adapter, channel, exten, caller_id, caller_id_name, action_id)  

    client.logoff()

    d['status'] = 'ok'
    d['id_ext'] = id_ext
    
    res = json.dumps(d, default=json_serial)

    USER_EVENTS[user] = {'id_ext': id_ext, 'id':id, 'user': user, 'channel':channel, 'exten':exten, 'caller_id':caller_id} 

    return res, 200, HEADERS

@app.route('/make_call_auto')
def make_call_auto():
    client = AMIClient(address=AMI_ADDRESS, port=AMI_PORT)
    future = client.login(username=AMI_USER, secret=AMI_SECRET)
    
    id = request.args.get('id', '') 
    exten = request.args.get('exten', '')
    file = request.args.get('file', '')
    action_id = request.args.get('action_id', '')

    exten = '8' + exten
    
    d = {}
    
    id_ext = uuid.uuid4()
    id_ext = str(id_ext)
    
    if future.response.is_error():
        d['status'] = 'failed'
        d['error'] = str(future.response)
        res = json.dumps(d, default=json_serial)
        
        return res, 200, HEADERS

    adapter = AMIClientAdapter(client)

    channel = f'Local/{exten}@ng_ext_autodial_speech_to_text'
    d['channel'] = channel

    variable = FILE_NAMES[file]

    res_call = do_call_without_oper(adapter, channel, DATA, APP, action_id, variable, exten)

    client.logoff()
    
    d = {}
                
    d['Действия'] = 'Asterisk_AutoCall_Event' 
    d['Данные'] = {} 
    d['Данные']['name'] = 'init' 
    d['Данные']['id_ext'] = id_ext
    d['Данные']['event_date'] = datetime.now()
    d['Данные']['status'] = 'ok'
    d['Данные']['callerid'] = exten
    d['Данные']['id'] = id.upper()
          
    jdata = json.dumps(d, default=json_serial)
                
    auto_call_event(jdata)

    AUTO_CALLS[channel] = {'id_ext': id_ext, 'id':id, 'channel':channel, 'exten':exten, 'callerid':exten} 

    #period =  datetime.now()
    #source = id.upper()
    #status = 'init'
    #value = id_ext
    #comment = res

    #var = Statuses_AutoCall.create(period=period, source=source, status=status, value=value, comment=comment)
    
    return jdata, 200, HEADERS

@app.route('/speech_to_text', methods=['GET', 'POST'])
def speech_to_text():
    if len(request.files) == 0:
        return '-1'
    
    callerid = request.args.get('callerid', '') 
    
    id = None

    for x in AUTO_CALLS:
        if callerid == AUTO_CALLS[x]['callerid']:
            id = AUTO_CALLS[x]['id']
            id_ext = AUTO_CALLS[x]['id_ext']

    _id_ext = str(id_ext).replace('-', '')
    
    topic = 'queries'

    url = f"""https://asr.yandex.net/asr_xml?uuid={_id_ext}&key={TOKEN}&topic={topic}&lang=ru-RU"""

    audio = request.files['audio'].stream.read()

    #headers={'Content-Type': 'audio/x-pcm;bit=16;rate=8000'}
    headers={'Content-Type': 'audio/x-wav'}
  
    response = requests.get(url, headers=headers, data=audio)

    answer = response.text

    comment = answer

    print(answer)

    res_parse = xmltodict.parse(answer)

    #res_str = json.dumps(res_parse, default=json_serial)

    recognition_res = res_parse.get('recognitionResults')

    res = '0'

    if not recognition_res is None:
        variants = recognition_res.get('variant')
        if not variants is None:
            if type(variants) == type([]):
                for var in variants:
                    answer = var.get('#text')
                    if not answer is None:
                        res = '0'
                         
                        if answer in ANSWERS_POSITIVE:
                            res = '1'
                        for x in ANSWERS_POSITIVE:
                            if x in answer:
                                res = '1'                       
                        
                        if answer in ANSWERS_NEGATIVE:
                            res = '2'
                        for x in ANSWERS_NEGATIVE:
                            if x in answer:
                                res = '2'
                        
                        if answer in ANSWERS_RE_RECORD:
                            res = '3'
                        for x in ANSWERS_RE_RECORD:
                            if x in answer:
                                res = '3'
                pass
            
            else:
                answer = variants.get('#text')
                if not answer is None:
                    res = '0'
                         
                    if answer in ANSWERS_POSITIVE:
                        res = '1'
                    for x in ANSWERS_POSITIVE:
                        if x in answer:
                            res = '1'     
                    
                    if answer in ANSWERS_NEGATIVE:
                        res = '2'
                    for x in ANSWERS_NEGATIVE:
                        if x in answer:
                            res = '2'

                    if answer in ANSWERS_RE_RECORD:
                        res = '3'
                    for x in ANSWERS_RE_RECORD:
                        if x in answer:
                            res = '3'
                pass
       
        else:
            res = '1'

    d = {}
                
    d['Действия'] = 'Asterisk_AutoCall_Event' 
    d['Данные'] = {} 
    d['Данные']['name'] = 'speech_to_text' 
    d['Данные']['id_ext'] = id_ext
    d['Данные']['id'] = id
    d['Данные']['res'] = res
    d['Данные']['comment'] = comment
    d['Данные']['event_date'] = datetime.now()
                
    jdata = json.dumps(d, default=json_serial)
                
    auto_call_event(jdata)

    return res

def callback_response(response):
    #print(response)
    return

def do_call_with_oper(adapter, channel, exten, caller_id, caller_id_name, action_id, timeout='', context=CONTEXT_LOCAL, priority=1, callback_response=None):
    res = adapter.Originate(Channel=channel, Context=context, Exten=exten, ActionID=action_id, Priority=priority,  CallerID=caller_id, CallerIDName=caller_id_name, Timeout=timeout, _callback=callback_response)

    return res

def do_call_without_oper(adapter, channel, data, app, action_id, variable = '', exten='', timeout=TIMEOUT_AUTO_DIAL, context=CONTEXT_AUTO_DIAL, callback_response=None):
    res = adapter.Originate(Channel=channel, Context=context, Application=app, Exten=exten, ActionID=action_id,  Data=data, Timeout=timeout, _callback=callback_response, Variable=variable)

    return res

def json_serial(obj):
    if isinstance(obj, (datetime, date)):
      return obj.isoformat()

    if isinstance(obj, decimal.Decimal):
      return float(obj)

    raise TypeError("Type is not serializable %s" % type(obj))

