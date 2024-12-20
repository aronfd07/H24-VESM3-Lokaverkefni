from machine import Pin, PWM, unique_id
from neopixel import NeoPixel
from random import randint
from time import sleep_ms
from binascii import hexlify
from umqtt.simple import MQTTClient
import asyncio

# -- WIFI --

WIFI_SSID = "TskoliVESM"
WIFI_LYKILORD = "Fallegurhestur"

def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(WIFI_SSID, WIFI_LYKILORD)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    
do_connect()
ai1 = Pin(18, Pin.OUT)
ai2 = Pin(17, Pin.OUT)
pwmA = PWM(Pin(16, Pin.OUT), 10000)

rofi = Pin(10, Pin.IN, Pin.PULL_UP)
np = NeoPixel(Pin(14), 48)

motor_on = False
ljos_on = bool(rofi.value())
ljos_litur = (255, 255, 255)
ljos_litur_birtu = (255, 255, 255)
ljos_birtustig = 1

def map_birtustig(x):
    global ljos_birtustig
    return round(int(x) * ljos_birtustig)

# -- MQTT --

def fekk_skilabod(topic, skilabod):
    global ljos_litur, ljos_litur_birtu, ljos_birtustig
    
    topic_str = topic.decode()
    skilabod_str = skilabod.decode()

    if topic_str == "Vasaljos/litur":
        rgb_strengur = skilabod_str[4:-1]
        rgb_listi = rgb_strengur.split(", ")
        ljos_litur = list(map(int, rgb_listi))
        ljos_litur_birtu = list(map(map_birtustig, rgb_listi))
    elif topic_str == "Vasaljos/birta":
        ljos_birtustig = 1 - abs(float(skilabod_str))
        ljos_litur_birtu = list(map(map_birtustig, ljos_litur))

MQTT_BROKER = "10.201.48.81" # eða broker.emqx.io (þarf að vera það sama á sendir og móttakara)
CLIENT_ID = hexlify(unique_id())
TOPIC_MOTOR = b"Vasaljos/#"
TOPIC_SENA = "sena"
mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER, keepalive=60)

async def mqtt_check():
    global mqtt_client
    
    while True:
        try:
            mqtt_client.check_msg()
        except Exception as excep:
            print(f"Villa: {excep}, endurtengist")
            mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER, keepalive=60)
            mqtt_client.set_callback(fekk_skilabod)
            mqtt_client.connect()
            mqtt_client.subscribe(TOPIC_MOTOR)
        await asyncio.sleep_ms(100)

mqtt_client.set_callback(fekk_skilabod)
mqtt_client.connect()
mqtt_client.subscribe(TOPIC_MOTOR)
mqtt_client.subscribe(TOPIC_SENA)

def slokkva():
    for i in range(48):
        np[i] = (0, 0, 0)
    np.write()


async def ljos_check():
    global motor_on, ljos_on
    ljos_on_sidast = 1
    while True:
        ljos_on = rofi.value()
        print(ljos_on)
        if not ljos_on and ljos_on_sidast:
            print("a")
            mqtt_client.publish(TOPIC_SENA, "1")
        if not ljos_on:
            ai1.value(1)
            ai2.value(0)
            pwmA.duty(1023)
        else:
            ai1.value(0)
            ai2.value(0)
        ljos_on_sidast = ljos_on
        for i in range(48):
            
                
            
            if not ljos_on:
                np[i] = ljos_litur_birtu
            else:
                np[i] = (0, 0, 0)
        np.write()
        
        await asyncio.sleep_ms(350)

async def main():
    asyncio.create_task(mqtt_check())
    asyncio.create_task(ljos_check())
    
    
    
    while True:
        await asyncio.sleep_ms(0)

asyncio.run(main())