import Adafruit_DHT
import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
import argparse
import statistics
import math
import random 
from datetime import datetime

parser = argparse.ArgumentParser(description='')
parser.add_argument("-c", "--client", type=str, default = 'garage_ambient_' + str(random.randint(0, 100000)), help='name of the mqtt client')

args = parser.parse_args()

MOSQUITO_CLIENT_NAME = args.client


# --------- BOARD CONFIGURATION ---------- #


thermostat_pin = 15


# --------- END CONFIGURATION ---------- #

def calculate_dew_point(T,RH):
  b = 17.62
  c = 243.12  
  try:
    return float((c*gamma_func(T,RH,b,c)) / (b - gamma_func(T,RH,b,c)))
  except Exception as e:
    print(e)
    return -10
    
def gamma_func(T,RH,b,c):
      return math.log(RH/100) + (b * T)/(c + T)
  
  
def on_connect(mqttc, obj, flags, rc):
    #print("rc: "+str(rc))
    pass

def on_publish(mqttc, obj, mid):
    #print("mid: "+str(mid))
    pass

def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))
        
def on_message(client, userdata, msg):
  msg_payload_decoded = msg.payload.decode("utf-8")
  

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
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.on_subscribe = on_subscribe
client.loop_start()

bathroom_temp_queue = [0,0,0,0,0,0,0,0,0,0]
bathroom_hum_queue = [0,0,0,0,0,0,0,0,0,0]

flag_first_cycle = True
queue_curr_index = 0
cumulative_ble_retry = 0

while True:
  try:
                      
    try:
      hum, temp = Adafruit_DHT.read_retry(11, thermostat_pin)
    except:
      print('Error in the dht thermostat')
      time.sleep(10)
      continue
    
    if flag_first_cycle:
      flag_first_cycle = False
      for i in range(len(bathroom_temp_queue)):
        bathroom_temp_queue[i] = temp
        bathroom_hum_queue[i] = hum
    else:
      bathroom_temp_queue[queue_curr_index] = temp
      bathroom_hum_queue[queue_curr_index] = hum
      queue_curr_index += 1
      if queue_curr_index >= len(bathroom_temp_queue):
        queue_curr_index = 0
        
    temp_bathroom_mean = statistics.mean(bathroom_temp_queue)
    hum_bathroom_mean = statistics.mean(bathroom_hum_queue)

    
    client.publish("ambient/bonate/garage/temperature", "{:.1f}". format(temp_bathroom_mean))
    client.publish("ambient/bonate/garage/humidity", "{:.1f}". format(hum_bathroom_mean))
    client.publish("ambient/bonate/garage/dew_point", "{:.1f}". format(calculate_dew_point(temp_bathroom_mean,hum_bathroom_mean)))
    time.sleep(60)
            

            
                 
  except Exception as e:
    print(e)
    bathroom_temp_queue = [0,0,0,0,0,0,0,0,0,0]
    bathroom_hum_queue = [0,0,0,0,0,0,0,0,0,0]

    flag_first_cycle = True
    queue_curr_index = 0
    time.sleep(15)
    
    
              