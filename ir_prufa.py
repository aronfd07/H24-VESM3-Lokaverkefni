from machine import Pin
from time import sleep_ms
from ir_rx.nec import NEC_8
from ir_tx.nec import NEC

ADDR = 1

def red_callback(data, addr, ctrl):
    # tékka hvort þetta sé okkar IR sendir með address
    if addr == ADDR:
        # kveikja á led
        if data == 1:
            print("kveikja")
        # slökkva á led
        elif data == 2:
            print("slökkva")

nec = NEC(Pin(12, Pin.OUT, value = 0))
red = NEC_8(Pin(13, Pin.IN), red_callback)

while True:
    nec.transmit(ADDR, 1)
    sleep_ms(500)
    nec.transmit(ADDR, 2)
    sleep_ms(500)
