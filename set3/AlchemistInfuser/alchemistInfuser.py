import chipwhisperer as cw
import numpy as np
import matplotlib.pyplot as plt
import time
import os


PLATFORM = "CWNANO"
PROG_TYPE = cw.programmers.STM32FProgrammer

TARGET_BIN_PATH = f"alchemistInfuser-CWNANO.hex"

################################################################################################################################################

# Connect to the CW
scope = cw.scope()

################################################################################################################################################

# Connect to the target
target = cw.target(scope, cw.targets.SimpleSerial)

################################################################################################################################################

# Setup the scope
scope.default_setup()

scope.adc.samples = 4000

################################################################################################################################################

# Program the target
cw.program_target(scope, PROG_TYPE, TARGET_BIN_PATH)

################################################################################################################################################

target.simpleserial_write('c', bytearray([78, 97, 74, 45, 85, 103, 82, 100, 50, 112, 88, 107, 56, 118, 53, 115]))
response = target.simpleserial_read('r', 17, timeout=2000)
print(response)

# Disconnect the oscope and the target
scope.dis()
target.dis()


