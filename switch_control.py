import RPi.GPIO as GPIO
import time
from  datetime import datetime
import os
import threading
import socket
import paho.mqtt.client as mqtt
import random

gate_remote_button = 7
error_led = 13

GPIO.setmode(GPIO.BOARD)
GPIO.setup(gate_remote_button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(error_led, GPIO.OUT)


MOSQUITO_CLIENT_NAME = socket.gethostname() +'_control_switch_mqtt_' +  str(random.randint(0, 100000))

TOPIC_COVER_SET = 'homeAssistant/casaBonate/cover/cancello/set'

def on_disconnect(client, userdata, rc):
    global not_connected
    not_connected = False
    GPIO.output(error_led, GPIO.LOW)
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
        GPIO.output(error_led, GPIO.HIGH)
        print(datetime.now())
        print('Im connected')
        time.sleep(2)
        client.on_disconnect = on_disconnect
        client.loop_start()

      except Exception as e:
        print(e)
        time.sleep(120)
  
      
connect_to_broker()



while True:
  try:
    if (GPIO.input(gate_remote_button) == 1 and not_connected == False):
      client.publish(TOPIC_COVER_SET , 'open')
      time.sleep(1)
    time.sleep(0.25) 
  except:
    pass
