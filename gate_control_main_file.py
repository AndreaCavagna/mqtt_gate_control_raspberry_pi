import time
import argparse
from datetime import datetime
import RPi.GPIO as GPIO
import threading
import socket
import paho.mqtt.client as mqtt
import random
from ping3 import ping

MOSQUITO_CLIENT_NAME = socket.gethostname() +'_control_gate_mqtt_' +  str(random.randint(0, 100000))


TOPIC_SUBSCRIBE = "homeAssistant/casaBonate/cover/cancello/set"
TOPIC_COVER_SET = 'homeAssistant/casaBonate/cover/cancello/set'
TOPIC_COVER_STATUS = "homeAssistant/casaBonate/cover/cancello/state"
TOPIC_COVER_AVAILABLE = "homeAssistant/casaBonate/cover/cancello/availability"
TOPIC_CONFIRM_ONLINE = "homeAssistant/casaBonate/cover/cancello/confirmOnline"

gate_operation_led = 15
gate_remote_relay = 8

error_led = 11

SHADE_STATUS = 'closed'
OPEN_LONG = False

HOLD_BUTTON_SEC = 1.2
RELAY_PRESS_REPETITIONS = 1

GPIO.setmode(GPIO.BOARD)

GPIO.setup(gate_remote_relay, GPIO.OUT)

GPIO.setup(gate_operation_led, GPIO.OUT)
GPIO.output(gate_operation_led, GPIO.LOW)
GPIO.setup(error_led, GPIO.OUT)

def fire_button(remote,sleep_between_fires=1,rep=1, HOLD_BUTTON_SEC = HOLD_BUTTON_SEC):
  for i in range(rep):
    GPIO.output(remote, GPIO.HIGH)
    time.sleep(HOLD_BUTTON_SEC)
    GPIO.output(remote, GPIO.LOW)
    if i is not rep-1:
      time.sleep(sleep_between_fires)

def gate_timing_control():
  fire_button(gate_remote_relay, sleep_between_fires=2, rep=RELAY_PRESS_REPETITIONS)


def blink_led_on_operation(duration: int, timeOn: float, timeOff: float, repetitions = 1, timeFinalPause = 0):
    time_end = time.time() + duration
    
    while time.time() < time_end:
        
        GPIO.output(gate_operation_led, GPIO.LOW)
        time.sleep(timeOn)
        GPIO.output(gate_operation_led, GPIO.HIGH)
        time.sleep(timeOff)

    time.sleep(timeFinalPause)

    GPIO.output(gate_operation_led, GPIO.HIGH)


def expose_topic_availability():
    
    while True:
      try:
        global not_connected
        global SHADE_STATUS
        time.sleep(60)
        
        if not_connected == False:
          client.publish(TOPIC_COVER_STATUS , SHADE_STATUS)
          client.publish(TOPIC_COVER_AVAILABLE , "online")
          GPIO.output(error_led, GPIO.LOW)
        else:
         GPIO.output(error_led, GPIO.HIGH)
        
      except Exception as e:
        print(e)
        GPIO.output(error_led, GPIO.HIGH)
        
        
def ping_router():
    while True:
      try:
        time.sleep(60)
    
        if ping('192.168.8.1'):
          GPIO.output(error_led, GPIO.LOW)
        else:
         GPIO.output(error_led, GPIO.HIGH)
        
      except Exception as e:
        print(e)
        GPIO.output(error_led, GPIO.HIGH)

def on_connect(mqttc, obj, flags, rc):
    #print("rc: "+str(rc))
    pass

def on_publish(mqttc, obj, mid):
    #print("mid: "+str(mid))
    pass

def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))
    pass
    
        
def on_message(client, userdata, msg):
  try:
    global OPEN_LONG
    global SHADE_STATUS
    global not_connected
    
    GPIO.output(error_led, GPIO.LOW)
    
    
    msg_payload_decoded = msg.payload.decode("utf-8")
    print("Message received-> " + msg.topic + " " + str(msg_payload_decoded))
    
    if msg.topic == TOPIC_COVER_SET and (msg_payload_decoded == 'open' or msg_payload_decoded == 'open_long') and not_connected == False:
     
     OPEN_LONG = False
     SHADE_STATUS = 'opening'
     GPIO.output(gate_operation_led, GPIO.LOW)
     t1 = threading.Thread(target = gate_timing_control, args=[])
     t1.start()
     if msg_payload_decoded == 'open_long':
       OPEN_LONG = True
       
     print('Sto aprendo il cancello')
     
     
    if msg.topic == TOPIC_CONFIRM_ONLINE and msg_payload_decoded == 'uThere?' and not_connected == False:
      client.publish(TOPIC_CONFIRM_ONLINE , 'Yep!')
      client.publish(TOPIC_COVER_STATUS , SHADE_STATUS)
     
  except Exception as e:
    print(e)
  


def on_disconnect(client, userdata, rc):
    global not_connected
    not_connected = False
    GPIO.output(error_led, GPIO.HIGH)
    print("I disconnected :(")
    try:
      client.loop_stop()
      time.sleep(3)
    except:
      print("I have stopped the loop")
    connect_to_broker()
    
    
    
    
def connect_to_broker():
    global not_connected
    global SHADE_STATUS
    global client
    not_connected = True
    while not_connected:
      try:
        client = mqtt.Client(MOSQUITO_CLIENT_NAME,clean_session=False)
        client.connect('myhomeipdk.hopto.org', port=1883)
        not_connected = False
        print(datetime.now())
        print('Im connected')
        time.sleep(2)
        SHADE_STATUS = 'closed'
        client.subscribe(TOPIC_SUBSCRIBE)
        client.subscribe(TOPIC_CONFIRM_ONLINE)
        client.subscribe(TOPIC_COVER_STATUS)
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        #client.on_connect = on_connect
        #client.on_publish = on_publish
        #client.on_subscribe = on_subscribe
        client.loop_start()
        
        time.sleep(2)
        client.publish(TOPIC_COVER_AVAILABLE , "online")
        client.publish(TOPIC_COVER_STATUS , SHADE_STATUS)
        time.sleep(2)
        client.publish(TOPIC_COVER_AVAILABLE , "online")
        GPIO.output(error_led, GPIO.LOW)
      except Exception as e:
        print(e)
        time.sleep(120)
  
      

connect_to_broker()



try:
  thread = threading.Thread(target = expose_topic_availability)
  thread.start()
  thread2 = threading.Thread(target = ping_router)
  thread2.start()
except Exception as e:
  print(e)

while True:
  try:
  
    
  
    if SHADE_STATUS == 'opening':
      GPIO.output(error_led, GPIO.LOW)
    
      if not_connected == False:
        client.publish(TOPIC_COVER_STATUS , SHADE_STATUS)
        
      blink_led_on_operation(45,1,1)
      
    
      SHADE_STATUS = 'open'
      
      if not_connected == False:
        client.publish(TOPIC_COVER_STATUS , SHADE_STATUS)
        
      GPIO.output(gate_operation_led, GPIO.HIGH)
      
      if OPEN_LONG == True:
        time.sleep(30)
        OPEN_LONG = False
        time.sleep(25)
      else:
        time.sleep(30)
    
    
      SHADE_STATUS = 'closing'
      
      if not_connected == False:
        client.publish(TOPIC_COVER_STATUS , SHADE_STATUS)
        
      blink_led_on_operation(45,0.2,0.2)
    
      SHADE_STATUS = 'closed'
      
      if not_connected == False:
        client.publish(TOPIC_COVER_STATUS , SHADE_STATUS)
    else:
      time.sleep(1)
    
  except Exception as e:
    print(e)
    time.sleep(5)

