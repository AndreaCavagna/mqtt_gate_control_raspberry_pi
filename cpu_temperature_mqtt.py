import os
import time
import socket
import paho.mqtt.client as mqtt
import psutil
import re
import subprocess
import shlex  
from subprocess import Popen, PIPE, STDOUT
import random
from datetime import datetime

REPETITIONS = 30
MOSQUITO_CLIENT_NAME = socket.gethostname() +'_cpu_temperature_mqtt_' +  str(random.randint(0, 100000))


def on_disconnect(client, userdata, rc):
    connect_to_broker()
    
    
def connect_to_broker():
    not_connected = True
    while not_connected:
      try:
        client.connect('myhomeipdk.hopto.org', port=1883)
        not_connected = False
        print(datetime.now())
        print('Im connected')
        time.sleep(10)
      except:
        print(datetime.now())
        print('Failed connection')
        time.sleep(3)
  
      
client = mqtt.Client(MOSQUITO_CLIENT_NAME)
connect_to_broker()
client.on_disconnect = on_disconnect
client.loop_start()


def read_wifi_strenght_from_cmd():
  p = subprocess.Popen("iwconfig", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out = p.stdout.read().decode()
  m = re.findall('(wlan[0-9]+).*?Signal level=(-[0-9]+) dBm', out, re.DOTALL) # ex. [('wlan0', '-21')]
  p.communicate()
  return m[0][1]
  
def get_simple_cmd_output(cmd, stderr=STDOUT):
    """
    Execute a simple external command and get its output.
    """
    args = shlex.split(cmd)
    return (Popen(args, stdout=PIPE, stderr=stderr).communicate()[0]).decode("utf-8") 

def get_ping_time(host):
    print('getting ping')
    host = host.split(':')[0]
    cmd = "fping {host} -C 10 -q".format(host=host)
    try:
      res_arr = get_simple_cmd_output(cmd).strip().split(':')[-1]
      res = 0
      for val in res_arr.strip().split(' '):
        res += float(val)
      res /= 10
    except Exception as e:
      print(e)
      res = 1000
    return res



while True:
  try:
    cpu_temp = 0
    cpu_usage = 0
    wifi_rssi = 0
    ping_time = get_ping_time('192.168.8.1')
    
    for i in range (REPETITIONS):
        cpu_temp += float( os.popen("cat /sys/class/thermal/thermal_zone0/temp").read() ) / 1000
        cpu_usage += int(psutil.cpu_percent())
        wifi_rssi += int(read_wifi_strenght_from_cmd())
        time.sleep(2)
        
    cpu_temp /= REPETITIONS
    cpu_usage /= REPETITIONS
    wifi_rssi /= REPETITIONS
    
    client.publish("homeAssistant/systemStatus/garage_cpu_temperature_mqtt/cpuTemp", "{:.1f}". format(cpu_temp))
    client.publish("homeAssistant/systemStatus/garage_cpu_temperature_mqtt/cpuUsage", "{:.1f}". format(cpu_usage))
    client.publish("homeAssistant/systemStatus/garage_cpu_temperature_mqtt/wifi_rssi", "{:.1f}". format(wifi_rssi))
    client.publish("homeAssistant/systemStatus/garage_cpu_temperature_mqtt/ping_time", "{:.1f}". format(ping_time))
  except Exception as e:
    print(e)
    time.sleep(30)
