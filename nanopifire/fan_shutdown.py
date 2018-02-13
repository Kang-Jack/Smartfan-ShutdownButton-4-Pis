#!/usr/bin/env python3
# Author: Andreas Spiess
# Modified for  Nano Pi 2 fire : Kang-Jack
import os 
import time 
from time import sleep 
import signal 
import sys
import context  # Ensures paho is in PYTHONPATH
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt



#import RPi.GPIO as GPIO
from ctypes import * 
lib = cdll.LoadLibrary('/usr/local/lib/libfahw.so') 
fanPin = 7 # The pin ID, edit here to change it 
powerSwitchPin = 12 
maxTMP = 50 #cpu usage up to 50%# The maximum temperature in Celsius after which we trigger the fan 
mqttc = mqtt.Client()
mqtt_server = "192.168.xxx.xxx"
mqtt_fan_on = 0
mqtt_shutdown = 0

def on_disconnect(client, userdata,rc=0):
    logging.debug("DisConnected result code "+str(rc))
    mqttc.loop_stop()

def on_message_fan(mosq, obj, msg):
    global mqtt_fan_on 
    value = str(msg.payload, encoding = "utf-8")
    print("fan: " + msg.topic + " " + str(msg.qos) + " " + value)
    if 'on' in value :
        print("fan: " + msg.topic + " " + str(msg.qos) + " " + value)
        mqtt_fan_on = 1
    if 'off' in value:
        print("fan: " + msg.topic + " " + str(msg.qos) + " " + value)
        mqtt_fan_on = 0

def on_message_power(mosq, obj, msg):
    global mqtt_shutdown    
    value = str(msg.payload, encoding = "utf-8")
    print("power: " + msg.topic + " " + str(msg.qos) + " " + value)
    if 'shutdown' in value:
        print("power: " + msg.topic + " " + str(msg.qos) + " " + value)
        mqtt_shutdown = 1

def on_message(mosq, obj, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
     

def Shutdown():
    fanOFF()
    #funcpwm=lib.unexportGPIOPin(fanPin)
    funcpwm=lib.unexportGPIOPin(powerSwitchPin)
    os.system("sudo shutdown -h")
    sleep(100) 
def setup():
    lib = cdll.LoadLibrary('/usr/local/lib/libfahw.so')
    funcpwm0=lib.boardInit()
    if funcpwm0<0: print ("Fail to init board")
    os.system("modprobe matrix_gpio_int")
    funcpwm=lib.exportGPIOPin(fanPin)
    funcpwm=lib.setGPIODirection(fanPin, 2) # pin 7,8,10 tested ; in = 1 out = 2
    funcpwm = lib.exportGPIOPin(powerSwitchPin)
    funcpwm = lib.setGPIODirection(powerSwitchPin, 1) # in =1 out =2
   
    # Add message callbacks that will only trigger on a specific subscription match.
    mqttc.message_callback_add("nano/control/fan/#", on_message_fan)
    mqttc.message_callback_add("nano/control/power/#", on_message_power)
    mqttc.on_message = on_message
    mqttc.connect(mqtt_server, 1883, 60)
    mqttc.subscribe("nano/control/#", 0)

    fanOFF()
    return() 
def getCPUtemperature():
    #res = os.popen('cat  /sys/class/hwmon/hwmon0/device/temp_label').readline()
    #res = os.popen('grep \'cpu \' /proc/stat | awk \'{usage=($2+$4)*100/($2+$4+$5)} END {print usage }\'').readline() #cpu average
    res = os.popen('top -b -n2 | grep \"Cpu(s)\" | awk \'{print $2+$4 }\' | tail -n1 ').readline() 	

    temp =res #(res.replace("'C\n",""))
    print("CPU usage is {0}".format(temp)) #Uncomment here for testing
    return temp 
def fanON():
    funcpwm=lib.setGPIOValue(fanPin, 1)
    publish.single("nano/status/fan", "Open", hostname = mqtt_server)
    return() 
def fanOFF():
    funcpwm=lib.setGPIOValue(fanPin, 0)
    publish.single("nano/status/fan", "Close", hostname = mqtt_server)    
    return() 

def handleFan():    
    str_temp = getCPUtemperature()
    CPU_temp = float(str_temp)
    print(mqtt_fan_on)
    if CPU_temp>maxTMP or mqtt_fan_on == 1 :
        fanON()
        print("fan on")
    if CPU_temp<maxTMP-5 and  mqtt_fan_on == 0:
        fanOFF()
        print("fan off")

    sleep(1) 
    publish.single("nano/status/cpu", str_temp, hostname = mqtt_server) 
    return() 

def handleBattery():
    #print (GPIO.input(powerSwitchPin))
    value = lib.getGPIOValue(powerSwitchPin)
    #print ("batteryPin:")
    #print(value)
    if value == 1 or mqtt_shutdown == 1:
        Shutdown()
    return()

#def setPin(mode): 
# A little redundant function but useful if you want to add logging
#    GPIO.output(fanPin, mode) return()
try:
    setup()
    mqttc.loop_start()
    while True:
        handleFan()
        handleBattery()
        sleep(4) # Read the temperature every 5 sec, increase or decrease this limit if you want 
except KeyboardInterrupt: # trap a CTRL+C keyboard interrupt
    fanOFF()
    #funcpwm=lib.unexportGPIOPin(fanPin)
    funcpwm=lib.unexportGPIOPin(powerSwitchPin)
    #GPIO.cleanup() # resets all GPIO ports used by this program
