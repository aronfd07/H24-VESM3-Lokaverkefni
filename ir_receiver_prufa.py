from machine import Pin
from ir_rx.nec import NEC_8
from time import sleep_ms

def red_callback(data, addr, ctrl):
    if data >= 0:
        print("Data: {:02x}, address: {:04x}".format(data, addr))

red = NEC_8(Pin(13, Pin.IN), red_callback)

while True:
    sleep_ms(100)