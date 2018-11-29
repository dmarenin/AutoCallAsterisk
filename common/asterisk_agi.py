# coding:utf8

import json, time, random
import gevent, gevent.queue, gevent.event
import socket, urllib

from datetime import datetime
import base64

from gevent.server import StreamServer
from gevent import monkey
monkey.patch_all(os = True, select = True)

################################################################################
### COMMON
################################################################################
def loop(self, socket, lim = '\r\n', *args):
  cbr = True
  func = self.cbfn
  def loop_send(command, data = {}, lim = lim, sync = True):
    return self.send(socket, command, data, lim, sync)

  while 1:
    data = ''
    while 1:
      try:
        buf = socket.recv(255)
      except:
        break
      data += buf
      #print data

      if type(self) == agi:
        gevent.sleep(0.01)

      if not buf or buf[-(len(lim)*2):] == lim+lim: break

    for d in data.split(lim+lim)[:-1]:
      pack    = makepack(d)
      print pack
      cbr = func(loop_send, pack, self.cmds, *args)

    if not data or not cbr: break

################################################################################
### Asterisk
################################################################################
class ami(object):
  def __init__(self, host, user, pswd, cbfn = None, port = 5038):
    self.ws   = None
    self.host = host
    self.port = port
    self.cbfn = self.ami_cb
    self._cbfn= cbfn
    self.user = user
    self.pswd = pswd
    self.cmds = {}

  def send(self, socket, command, data = {}, lim = '\r\n'):
    if type(data) in (str, unicode):
      data = {'text': data}
    elif data == None:
      data = {}

    packet = ""

    data['action'] = command

    if data.get('actionid') == None:
      data['actionid'] = str(time.time() + random.random())

    self.cmds[data['actionid']] = data

    for k, v in data.items():
        packet += '%s: %s%s' % (k, str(v), lim)

    packet += lim

    if len(data) == 0:
      socket.send(command + lim + lim)
    else:

      socket.send(packet)

    return data['actionid']

  def ami_cb(self, send, pack, cmds):
    ename   = pack.get('event')
    chain   = pack.get('channel1') or pack.get('channel')
    caller  = pack.get('callerid1') or pack.get('calleridnum')
    called  = pack.get('callerid2') or pack.get('connectedlinenum')
    estate  = pack.get('bridgestate')
    action  = pack.get('action')

    aid = pack.get('actionid')
    if aid:
      if self.cmds.get(aid):
        pack.update(self.cmds[aid])
        if action and action != 'bridge':
          del self.cmds[aid]


    #if pack.get('response'):
    #  if conf.debug_ami:
    #    if pack.get('response') == "Success":
    #      lvl = debug.magenta
    #    else:
    #      lvl = debug.red

    #    if action:
    #        pass


    elif self._cbfn != None:
      self._cbfn(send, pack, cmds)

    else: 
      #print chain, caller, called, ename

      pass

    return True

      
  def connect(self):
    def handler():
      self.ws = socket.socket()
      self.ws.connect((self.host, self.port))
      
      self.send(self.ws, 'Login', {'username': self.user, 'secret': self.pswd, 'events': 'on'})
      loop(self, self.ws, '\r\n')
      self.ws.close()
      
      gevent.sleep(0.5)

    if conf.debug_ami:
      handler()
    else:
      while True:
        try:
          handler()
        except Exception as e:
            pass

        gevent.sleep(60)

################################################################################
class agi(object):
  def __init__(self, cbfn=None, port = 4573, addr = '192.168.7.220'):
    self.cbfn = agi_callback
    self.addr = addr
    self.port = port 
    self.cmds = {}
    self.sock = None

    server = StreamServer((self.addr, self.port), self.__agi_connect)

    server.serve_forever()

  def send(self, socket, command, data = {}, lim = '\r\n', sync = True):
    
     

    if command == 'close':
      pass
      
      return socket.close()

    socket.send(command + lim)
    r = True

    while sync:
      try:
        r = socket.recv(1024)
      except Exception as e:
        return ''

      r = r.strip().split(' ')
      r = [ r[0], ' '.join(r[1:]) ]
    
      if r[0] in ('200', '511'):
   
         
        break
      else:
          pass

          

    return r

  def __agi_connect(self, socket, address):
    self.sock = socket
    loop(self, socket, '\n')
    #socket.close()

def makepack(data):
  pack = {}
  for line in data.splitlines():
    if line == '': continue
    s = line.split(': ', 1)
    k = str(s[0])
    if len(s) == 1:
        pack[k.lower()] = None
    else:
        pack[k.lower()] = s[1]
  return pack

def mk_rec_path(caller, called, direction = 'transfer'):
  return conf.rec.format(datetime.now()) % (direction, caller, called)

def encrypt(key, clear):
  enc = []
  for i in range(len(clear)):
    key_c = key[i % len(key)]
    enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
    enc.append(enc_c)
  enc = base64.urlsafe_b64encode("".join(enc))
  return enc

def decrypt(key, enc):
  dec = []
  enc = base64.urlsafe_b64decode(enc)
  #debug.log(key, enc)
  for i in range(len(enc)):
      key_c = key[i % len(key)]
      dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
      dec.append(dec_c)
  clear = "".join(dec)
  return clear

def agi_callback(send, pack, cmds):
    cs = pack.get('agi_network_script').split("#")
    k = 1
    for c in cs[1:]:
      pack['agi_arg_%d' % k] = c
      k += 1

    command = cs[0]

    #if conf.debug_agi:
    #  debug.log("AGI:", command, pack.get('agi_channel'), level = debug.cyan, backtrace = False)

    if   command == 'auth':       agi_auth     (send, pack)
    elif command == 'external':   agi_external (send, pack)
    elif command == 'inbound':    agi_inbound  (send, pack)
    elif command == 'outbound':   agi_outbound (send, pack)
    #else:                         debug.log (pack, level = debug.blue)

    return False

def agi_auth         (send, pack):
    #caller = pack.get('agi_callerid')
    #pin = pack.get('agi_arg_1')

    #Verbose(0,=> Outbound  :  ${CALLERID(num)}        =>  ${EXTEN})
    #send('exec Dial "SIP/ng_ext/89324817245,,g,"')
    
    #send('exec playback /usr/local/share/asterisk/moh/agrad/auto/sps')
    #Playback(/usr/local/share/asterisk/moh/agrad/auto/sps)

#    if ones.phone_auth(caller, pin):
    send('exec playback tt-somethingwrong')
#      send('exec playback vm-goodbye')
#    else:
    #send('exec playback /usr/local/share/asterisk/moh/agrad/auto/auto_ford')
    #send('exec playback vm-goodbye')
    #send('exec playback vm-goodbye')

#def agi_external     (self, send, pack):
#    caller = pack.get('agi_callerid')

#    if len(caller) > 6:
#      caller = caller[6:10]

#    called = pack.get('agi_arg_1')

#    rpath = common.mk_rec_path(caller, called, 'external')
#    self.ami_send('mixmonitor', {
#      'file'    : 'recordings/%s' % rpath,
#      'channel' : pack.get('agi_channel'),
#      }
#    )

#    debug.log(caller, called, rpath)
#    ones.push('OutCall', {'caller': caller, 'called': called, 'rpath': rpath })
#    send('close') 
#def transfer(self, call, send):
#    managers = []
#    managers.append('7099')
#    managers.append('7096')
#    while 1:
#      if managers:
#        dstring = 'exec dial '
#        for m in managers:
#          dstring += 'SIP/%s,%d&' % (m, conf.cc_timeout)
#        debug.log("OK", dstring)
#        send(dstring)
#        debug.log("OK")
#        return
#      else:
#        gevent.sleep(5)

#def agi_inbound      (self, send, pack):
#    call        = Call(pack, send)
#    call.record()
#    self.push(call)
    
#    send('answer')
#    gevent.sleep(0.5)

#    # TODO
#    #self.transfer(call, send)
#    
#    if self.users.queue(call, send) == False:

#      exten = pack.get('agi_arg_1')

#def agi_outbound     (self, send, pack):
#    call          = Call(pack, send, 'outbound')
#    call.record()
#    self.push(call)

#    user = self.users.get_user_by_sip(call.caller)

#    if user:
#      user.assign(call)

#      #send('exec gosub sub_outbound,%s,1' % call.called) # не блокирующий вызов
#      # нужно отслеживать состояние канала
#      # невозможно отправить сообщения в AGI канал после выхода из этой функции
#      #while (call.e_status != 'hangup'): # колхоз "Красный Лапоть"
#      #  gevent.sleep(3)

#      #send('exec dial SIP/%s' % call.called) # не позволяет использовать
#      # адресацию в диалплане - нужно сразу указывать на какую технологию 
#      # отправлять звонок

#      #send('gosub sub_outbound %s 1' % call.called) # блокирующий вызов
#      # не позволяет вызвать Return из диалплана если вызывающий кладет трубку
#      # засыпает нотайсами лог Астериска

#      # нельзя оставить здесь если вызов не блокирующий
#      #user.unassign(call) 

#      # отметка о выходе из блокировки
#      #debug.log("OK", level = debug.red, backtrace = False)

#      # РЕШЕНИЕ
#      # не вызывать диалплан из AGI
#      # выполнять только необходимые вызовы
#      # - запись разговора
#      # - ???
#      # - PROFIT!!
#    else:
#      debug.log("NO USER by caller %s" % call.caller, level = debug.error)

#    #self.pop(call)

#def by_tag(self, tag):
#    for k, call in self.active.items():
#      #call = call['agi']
#      if conf.debug_xfer:
#        debug.log(tag, ' <-> ', k, '[', call.tag, ']', backtrace = False)
#      if call.tag == tag:
#        return call

#  # returns Result, ResponseText, RecordPath
#def bridge(self, aleg, bleg):
#    if not aleg:
#      return "Ошибка. Отсутствует тег источника соединения", None
#    if not bleg:
#      return "Ошибка. Отсутствует тег назначения соединения", None

#    aleg = self.by_tag(aleg)
#    bleg = self.by_tag(bleg)

#    if type(aleg) != Call:
#      return "Ошибка. Неизвестный источник соединения", None
#    if type(bleg) != Call:
#      return "Ошибка. Неизвестное назначение соединения", None

#    cnt = 0 # ждем до пяти секунд, если AMI еще не получила тег назначения
#    while cnt < 5 and not bleg.bid:
#      gevent.sleep(1)
#      cnt += 1

#    if not aleg.aid:
#      return "Ошибка. Отсутствует цепочка источника соединения", None
#    if not bleg.bid:
#      return "Ошибка. Отсутствует цепочка назначения соединения", None

#    gevent.sleep(0.5)

#    actionid = self.ami_send('bridge', {
#      'channel1'      : aleg.aid,
#      'channel2'      : bleg.bid,
#      'tone'          : 'yes', # уведомление менеджера о начале связи
#      }
#    )

#    while cnt < 10:
#      pack = self.ami.cmds.get(actionid)
#      #debug.log(type(pack), bool(pack), pack)

#      while not pack:
#        debug.log("Трансфер  %s ?-? %s" % (
#          aleg.caller,
#          bleg.called
#          ), level = debug.warning, backtrace = False)
#        gevent.sleep(1)
#        #return "Ошибка соединения (идентификатор отсутствует в пакете команд)"

#      r = pack.get('response')

#      if r == "Success": break
#      elif r:
#        debug.log("Трансфер  %s X-X %s" % (
#          aleg.caller, bleg.called
#          ), level = debug.warning, backtrace = False)
#        return "Ошибка соединения: " + pack.get('response'), None

#      cnt += 1

#    del self.ami.cmds[actionid]

#    #self.ami_send('playdtmf', {
#    #  'channel' : bleg.bid,
#    #  'digit'   : '0',
#    #  }
#    #)

#    rpath = common.mk_rec_path(aleg.caller, bleg.called)
#    self.ami_send('mixmonitor', {
#      'file'    : 'recordings/%s' % rpath,
#      'channel' : bleg.bid,
#      }
#    )

#    debug.log("Трансфер  %s <-> %s" % (
#      aleg.caller,
#      bleg.called
#      ), level = debug.info, backtrace = False)

#    return "Соединение завершено", rpath


_agi = agi()

