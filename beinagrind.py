import network
import time
import machine
from umqtt.simple import MQTTClient
import ujson
import neopixel
from machine import Pin, PWM, unique_id
import asyncio
from servo import Servo
from binascii import hexlify
from lib.dfplayer import DFPlayer

servo_pin_v = Pin(4)  
servo_pin_h = Pin(6)  
servo_pin_upp_nidur = Pin(10)
servo_pin_til_hlidar = Pin(12)
servo_pin = Pin(15) 
servo_kjalki = Servo(servo_pin, freq=50, min_us=600, max_us=2400, angle=180)

servo_til_hlidar = Servo(servo_pin_til_hlidar, freq=50, min_us=600, max_us=2400, angle=180)
servo_upp_nidur = Servo(servo_pin_upp_nidur, freq=50, min_us=600, max_us=2400, angle=180)
servo_v = Servo(servo_pin_v, freq=50, min_us=600, max_us=2400, angle=180)
servo_h = Servo(servo_pin_h, freq=50, min_us=600, max_us=2400, angle=180)

df = DFPlayer(2)
df.init(tx=17, rx=16)

rgb1_pins = {
    "red": Pin(40, Pin.OUT),
    "green": Pin(41, Pin.OUT),
    "blue": Pin(42, Pin.OUT)
}

rgb2_pins = {
    "red": Pin(36, Pin.OUT),
    "green": Pin(35, Pin.OUT),
    "blue": Pin(37, Pin.OUT)
}

WIFI_SSID = "TskoliVESM"
WIFI_PASSWORD = "Fallegurhestur"
MQTT_BROKER = "10.201.48.81"
MQTT_CLIENT_ID = hexlify(unique_id())
TOPIC_V_HENDI = "2807hendiV"
TOPIC_H_HENDI = "2807hendiH"
TOPIC_AUGU = "Haus/lysa_augu"
TOPIC_HLJOD = "Haus/hljod"
TOPIC_BLIKK_HRADI = "Haus/augu_hradi"
TOPIC_UPP_NIDUR = ""
TOPIC_TIL_HLIDAR = ""
TOPIC_KJALKI = "Haus/kjalki"

'''
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        raise ValueError("Invalid HEX color format. Must be in #RRGGBB format.")
    r = int(hex_color[0:2], 16) > 0
    g = int(hex_color[2:4], 16) > 0
    b = int(hex_color[4:6], 16) > 0
    return r, g, b
'''

def set_rgb_green(rgb_pins_1, rgb_pins_2):
    rgb_pins_1["red"].value(0)
    rgb_pins_1["green"].value(1)
    rgb_pins_1["blue"].value(0)
    rgb_pins_2["red"].value(0)
    rgb_pins_2["green"].value(1)
    rgb_pins_2["blue"].value(0)


blink_task = None 
rgb_on = False
def set_rgb_color(rgb_pins, r, g, b):
    rgb_pins["red"].value(r)
    rgb_pins["green"].value(g)
    rgb_pins["blue"].value(b)

def set_all_rgb(rgb_pins_1, rgb_pins_2, state):
    rgb_pins_1["red"].value(state)
    rgb_pins_1["green"].value(state)
    rgb_pins_1["blue"].value(state)
    rgb_pins_2["red"].value(0)
    rgb_pins_2["green"].value(state)
    rgb_pins_2["blue"].value(state)

async def blink_rgb(rgb_pins_1, rgb_pins_2, delay):
    while True:
        if rgb_on:
            set_all_rgb(rgb_pins_1, rgb_pins_2, 1)  # Turn ON
            await asyncio.sleep(delay / 2)
            set_all_rgb(rgb_pins_1, rgb_pins_2, 0)  # Turn OFF
            await asyncio.sleep(delay / 2)
        else:
            set_all_rgb(rgb_pins_1, rgb_pins_2, 0)  
            await asyncio.sleep(0.1)  

'''
async def play_music():
    
    await asyncio.sleep(1)
    await df.wait_available()
    await df.volume(20)
    await df.play(1, 1)
'''
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        time.sleep(0.5)
    print("Wi-Fi connected:", wlan.ifconfig())

async def play_music():
    try:
        await df.wait_available()
        await df.volume(20)
        print("Playing audio...")
        await df.play(1, 1) 
    except Exception as e:
        print("Error playing audio:", e)

async def stop_music():
    try:
        await df.wait_available()
        await df.stop()
        print("Audio playback stopped.")
    except Exception as e:
        print("Error stopping audio:", e)

def mqtt_callback(topic, msg):
    global blink_task
    global rgb_on
    topic = topic.decode("utf-8")
    msg = msg.decode("utf-8")
 
    if topic == TOPIC_V_HENDI or topic == TOPIC_H_HENDI:
        try:
            msg = int(msg)
            print(msg)
        except ValueError:
            print("Received invalid message, skipping...")
            return

        angle = round(msg)
        #print(angle)
        if topic == TOPIC_V_HENDI:
            angle = angle * -1
            print(angle)
            servo_v.write_angle(angle)
        elif topic == TOPIC_H_HENDI:
            print(angle)
            servo_h.write_angle(angle)
    
    elif topic == TOPIC_UPP_NIDUR or topic == TOPIC_TIL_HLIDAR:
        try:
            msg = int(msg)
            print(msg)
        except ValueError:
            print("Received invalid message, skipping...")
            return

        angle = round(msg)
        if topic == TOPIC_UPP_NIDUR:
            print(angle)
            servo_upp_nidur.write_angle(angle)
        elif topic == TOPIC_TIL_HLIDAR:
            print(angle)
            servo_til_hlidar.write_angle(angle)
    elif topic == TOPIC_KJALKI:
        print(msg)
        try:
            msg = int(msg)
            print(msg)
        except ValueError:
            print("Received invalid message, skipping...")
            return
        angle = round(msg)
        print(angle)
        servo_kjalki.write_angle(angle)
    elif topic == TOPIC_AUGU:
        if msg == "true":
            set_all_rgb(rgb1_pins, rgb2_pins, 1)  # 1 = ON
            rgb_on = True
        elif msg == "false":
            set_all_rgb(rgb1_pins, rgb2_pins, 0)  # 0 = OFF
            rgb_on = False
    elif topic == TOPIC_BLIKK_HRADI:
 
        try:
            delay = float(msg)
            if delay <= 0.5:  # Lágmarkshraði, stillt á 50ms (0.05s)
                delay = 0.5
                print("0.5")
            print(delay)
            if blink_task is not None:
                blink_task.cancel()  # Hætta við fyrri verkefni ef það er til
            blink_task = asyncio.create_task(blink_rgb(rgb1_pins, rgb2_pins, delay))
        except ValueError:
            print("Invalid message for blink speed. Must be a number.")
    
    elif topic == TOPIC_HLJOD:
        if msg == "true":
            asyncio.create_task(play_music())
        elif msg == "false":
            asyncio.create_task(stop_music())
    

    
def connect_mqtt():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(TOPIC_V_HENDI)
    client.subscribe(TOPIC_H_HENDI)
    client.subscribe(TOPIC_AUGU)
    client.subscribe(TOPIC_BLIKK_HRADI)
    client.subscribe(TOPIC_HLJOD)
    client.subscribe(TOPIC_KJALKI)
    print("Tengdur við MQTT broker:", MQTT_BROKER)
    return client

async def mqtt_loop(client):
    while True:
        client.check_msg()
        await asyncio.sleep(0.1)

async def main():
    connect_wifi()
    client = connect_mqtt()
    await mqtt_loop(client)

asyncio.run(main())