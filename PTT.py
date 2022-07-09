import time
import RPi.GPIO as GPIO
from Codec import Codec
from Tools import suppress_stdout

PTT_PIN = 17
PULSE_TIME=0.04#0.05

pins = {}
def toggle(pin):
    if pin not in pins.keys():
        pins[pin] = False
        GPIO.setup(pin, GPIO.OUT)
    
    pins[pin] = not pins[pin]
    
    GPIO.output(pin, pins[pin])


def on_off(times, delay):
    for i in range(times):
        toggle(PTT_PIN)
        time.sleep(delay)


def send_bits(bits, delay):
    for bit in bits:
        if bit and not pins[17]:
            toggle(17)
        elif not bit and pins[17]:
            toggle(17)
        
        time.sleep(delay)

def main():
    print(f"Pulse Delay: {PULSE_TIME}")
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    #sync pulses
    on_off(30, PULSE_TIME)

    # 2 high bits == start read
    toggle(17)
    time.sleep(PULSE_TIME*2)
    toggle(17)

    FLAG = "01111110"


    while True:
        inp = input(">")

        start_time = time.time()

        msg = ''.join(format(ord(x), '08b') for x in inp)


        #msg = "11001010010110"
        #frame = ""
        #msg = "10001010001"

        bits = Codec.encode_manchester(Codec.str_to_boolarr(FLAG + msg + FLAG))
        #print(Codec.boolarr_to_str(bits))
        #print(FLAG + " " + msg + " " + FLAG)
        send_bits(bits, PULSE_TIME)

        if pins[17]:
            toggle(17)
    
        end_time = time.time()

        print(f"sent {len(msg)} bits of data in {end_time - start_time} seconds\n")


if "__main__" in __name__:
    main()