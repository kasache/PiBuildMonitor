import io
import time
import sys
import threading
import RPi.GPIO as IO
from subprocess import call, Popen, PIPE
import SimpleHTTPServer
import SocketServer
from threading import Thread
from subprocess import call

VERBOSE = 0

def prnt(text):
  if(VERBOSE and text):
    print(text)

def sysCall(cmd):
  try:
    print('call ' + cmd)
    res = call(cmd.split())
    print('call result ' + str(res))
  except Exception as e:
    print(e)
  #

def asyncSysCall(cmd,async=False):
  print('asyncSysCall ' + cmd + ' async=' + str(async))
  if(async):
    t = Thread(target=sysCall, args=(cmd,))
    t.start()
  else:
    sysCall(cmd)



def getDriveUse():
  u = '?%'
  try:
    cmd = 'df'
    output,error = Popen(cmd.split(),stdout = PIPE, stderr=PIPE).communicate()
    u = output.split()[11]
  except Exception as e:
    prnt(e)
  return u

def getCpuTemp():
  #vcgencmd measure_temp
  u = 50.0
  try:
    cmd = 'vcgencmd measure_temp'
    output,error = Popen(cmd.split(),stdout = PIPE, stderr=PIPE).communicate()
    temp = output.split('=')[1]
    temp = temp.split("'")[0]
    u = float(temp)
  except Exception as e:
    prnt(e)
  print('getCpuTemp ' + str(u))
  return u

def getCPUuse():
  u = (str(Popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip()))
  print("getCPUuse " + u)
  return u

def makeWav(file, text):
  cmd = ('pico2wave -w=' + file + ' -l=de-DE "' + text + '"')
  asyncSysCall(cmd)

def playWav(file):
  cmd = ('aplay '+file)
  asyncSysCall(cmd)

	
class DuoLed:
  def __init__(self,r,g,io):#(Pin Rot, Pin Gruen, GPIO)
    self.r = r
    self.g = g
    self.IO = io
  def off(self):
    self.IO.output((self.r,self.g),0)
  def red(self):
    self.IO.output((self.r,self.g),0)
    self.IO.output(self.r,1)
  def grn(self):
    self.IO.output((self.r,self.g),0)
    self.IO.output(self.g,1)
  def ylw(self):
    self.IO.output((self.r,self.g),0)
    self.IO.output((self.r,self.g),1)
  def set(self, color):
    #r|R = red
    #y|Y = red
    #g|G = red
    #r|R = red
    if(color == '0' or color == 'o' or color == 'O'):
      self.IO.output((self.r,self.g),0)
    elif(color == 'r' or color == 'R'):
      self.IO.output((self.g),0)
      self.IO.output((self.r),1)
    elif(color == 'g' or color == 'G'):
      self.IO.output((self.r),0)
      self.IO.output((self.g),1)
    elif(color == 'y' or color == 'Y'):
      self.IO.output((self.r,self.g),1)
  #class DuoLed

status=1
I0 = 24
I1 = 26
QAR = 7
QAY = 5
QAG = 3
Q0r = 8
Q0g = 10
Q1r = 12
Q1g = 11
Q2r = 13
Q2g = 15
Q3r = 19
Q3g = 21
Q4r = 23
Q4g = 16
QBerry = 18
QRel = 22
L0 = DuoLed(Q0r,Q0g,IO)
L1 = DuoLed(Q1r,Q1g,IO)
L2 = DuoLed(Q2r,Q2g,IO)
L3 = DuoLed(Q3r,Q3g,IO)
L4 = DuoLed(Q4r,Q4g,IO)

eHlt = threading.Event()
eBtn = threading.Event()

ch_list = [QAR,QAY,QAG,Q0r,Q0g,Q1r,Q1g,Q2r,Q2g,Q3r,Q3g,Q4r,Q4g,QRel]
PORT = 80

isAlive = 0

def setLeds(leds):
  print('setLeds' + str(bin(leds)))
  if(status > 0):
    IO.output(Q0r,(leds>>1)&1)
    IO.output(QRel,(leds>>0)&1)
    IO.output(Q0g,(leds>>0)&1)
    IO.output(Q1r,(leds>>3)&1)
    IO.output(Q1g,(leds>>2)&1)
    IO.output(Q2r,(leds>>5)&1)
    IO.output(Q2g,(leds>>4)&1)
    IO.output(Q3r,(leds>>7)&1)
    IO.output(Q3g,(leds>>6)&1)

def ampel(ryg):
  if(status > 0):
    if(ryg == 'r' or ryg == 'R'):
      IO.output([QAR],1)
    elif(ryg == 'y' or ryg == 'Y'):
      IO.output([QAY],1)
    elif(ryg == 'g' or ryg == 'G'):
      IO.output([QAG],1)
    elif(ryg == 'o' or ryg == 'O' or ryg == '0'):
      IO.output([QAY,QAG],0)


def alarm(al):
  if(status > 0):
    if(al == 'on' or al == '1'):
      IO.output(QRel,1)
    elif(al == 'off' or al == 'o' or al == 'O' or al == '0'):
      IO.output(QRel,0)

def setAlive():
  global isAlive
  if(isAlive<3):
    isAlive = isAlive+1

def alive():
  if(status > 0):
    if(isAlive > 1):
      IO.output([QAG],1)
    else:
      IO.output([QAG],0)
      IO.output([QAR],1)

def status(st):
  if(status > 0):
    ls = list(st)
    L0.set(ls[0])
    L1.set(ls[1])
    L2.set(ls[2])
    L3.set(ls[3])
    L4.set(ls[4])
    ampel(ls[5])
    alarm(ls[6])

class MyRequestHandler (SimpleHTTPServer.SimpleHTTPRequestHandler):
  def do_GET(self):
    print('hallo ' + self.path)
    self.protocol_version='HTTP/1.1'
    self.send_response(200, 'OK')
    self.send_header('Content-type', 'text/html')
    self.end_headers()
    html="<html> <head><title> Build Monitor </title> </head><body>CPU: " + str(getCpuTemp()) + "C <br></body></html>"
    if(self.path.find("/cgi-bin/setBuildStatus.py?leds=") >= 0):
      strLeds = self.path.split('=')[1]
      leds = 0
      print('getval ' + strLeds)
      try:
        print('dec')
        leds = int(strLeds)  # dec
      except ValueError:
        print('hex')
        leds = int(strLeds, 16)  # hex
      finally:
        setLeds(leds)
    elif(self.path.find("ampel=") >= 0):
      ryg = self.path.split('=')[1]
      ampel(ryg)
    elif(self.path.find("alarm=") >= 0):
      al = self.path.split('=')[1]
      alarm(al)
    elif(self.path.find("status=") >= 0):
      st = self.path.split('=')[1]
      status(st)
    elif(self.path.find("alive") >= 0):
      #build rechner muss sich melden
      setAlive()
    elif(self.path.find("setClock=") >= 0):
      t = self.path.split('=')[1]
      setClock(t)
    elif(self.path.find("makeWav=") >= 0):
      s = self.path.split('=')
      makeWav(s[1],s[2])
    elif(self.path.find("playWav=") >= 0):
      s = self.path.split('=')[1]
      playWav(s)
    elif(self.path.find("halt") >= 0):
      asyncSysCall('halt')
    elif(self.path.find("reboot") >= 0):
      asyncSysCall('reboot')
    elif(self.path.find("setTime") >= 0):
      t = self.path.split('=')[1]
      asyncSysCall('date --set="' + t + '"')
    else:
      html="<html> <head><title> Build Monitor </title> </head> <body>CPU: " + str(getCpuTemp()) + "C <br>usage:<br>http://172.16.0.74/cgi-bin/setBuildStatus.py?leds=0<br>http://rpi/ampel=r|y|g<br>http://rpi/alarm=on<br>http://rpi/alive (ca. jede Stunde)<br>http://rpi/status=RYGRYG1<br>http://rpi/setTime=29 july 2015 17:11:00<br></body></html>"
    self.wfile.write(html)

  
  def do_POST(self):
    logging.error(self.headers)
    form = cgi.FieldStorage(
    fp=self.rfile,
    headers=self.headers,
    environ={'REQUEST_METHOD':'POST','CONTENT_TYPE':self.headers['Content-Type'],})
    for item in form.list:
      logging.error(item)
    SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)


Handler = MyRequestHandler
HTTPD = SocketServer.TCPServer(("", PORT), Handler)

	
def in_cllbck(ch):
  print('in_cllbck ' + str(ch) + str(IO.input(ch)))
  if(IO.input(I1)):
    eHlt.set()
  elif(IO.input(I0)):
    IO.output(ch_list,0)

def startHttpd():
  global status
  try:
    print "serving at port", PORT
    HTTPD.serve_forever()
  except Exception as e:
    print('startHttpd exc' + str(e))
    status = -1

def sysCall(cmd):
  try:
    call(cmd.split())
  except Exception as e:
    print(e)

def heartBeat():
  while(status != 0):
    on=0.5
    #getCPUuse()
    #off=(((60.0/(getCpuTemp()-20)))*1.5)-on
    off=(60.0/getCpuTemp())-on
    if(off>0.0):
      IO.output(QBerry,0)
      time.sleep(off)
    IO.output(QBerry,1)
    time.sleep(on)
  #

#der build Rechner muss sich jede Minute mit "alive" melden, sonst ist die Ampel rot
def checkAlive():
  global isAlive
  i=0
  while(status != 0):
    time.sleep(1.0)
    if(i>7200):
      i=0
      isAlive = isAlive-1
    if(isAlive < 0):
      isAlive = 0
    i = i+1
    alive()

def init():
  print('init PI ' + str(IO.RPI_REVISION) + ' V'  + str(IO.VERSION))
  IO.setmode(IO.BOARD)
  IO.setup(I0,IO.IN,pull_up_down=IO.PUD_DOWN)
  IO.add_event_detect(I0, IO.BOTH, callback=in_cllbck, bouncetime=50)
  IO.setup(I1,IO.IN,pull_up_down=IO.PUD_DOWN)
  IO.add_event_detect(I1, IO.BOTH, callback=in_cllbck, bouncetime=50)  
  IO.setup(QBerry, IO.OUT)
  IO.setup(ch_list, IO.OUT)
  IO.output(ch_list,0)
  t = Thread(target=startHttpd)
  t.setDaemon(1)
  t.start()
  t1 = Thread(target=heartBeat)
  t1.setDaemon(1)
  t1.start()
  t2 = Thread(target=checkAlive)
  t2.setDaemon(1)
  t2.start()
  eHlt.clear()

def exit():
  print('exit')
  HTTPD.shutdown()
  IO.cleanup()

def main():
  global status
  err = 0
  try:
    print('main')
    init()
    IO.output(QBerry,1)
    eHlt.wait()
  except Exception as e:
    print('main exc: ' + str(e))
    err = 1
  
  status = 0
  #warten bis alle zyklischen threads das ende mitbekommen
  time.sleep(1.0)
  exit()
  #if(err == 0):
  #  sysCall('halt')

if __name__ == "__main__":
  main()
