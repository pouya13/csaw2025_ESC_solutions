import chipwhisperer as cw
import numpy as np
import matplotlib.pyplot as plt
import math

PLATFORM = "CWNANO"
PROG_TYPE = cw.programmers.STM32FProgrammer

#TARGET_BIN_PATH = f"../../targets/echoesOfChaos/echoesOfChaos-{PLATFORM}.hex"
TARGET_BIN_PATH = f"../../../csaw_esc_2025/challenges/set3/chaos-CWNANO.hex"

GET_PT_RESPONSE_LEN = 1
RESET_RESPONSE_LEN = 1
NUM_Q_RESPONSE_LEN = 4

FLAG_LEN = 20

THRESHOLD = 1.0

# Sets up scope and target
def cw_setup():
    scope = cw.scope()
    target = cw.target(scope, cw.targets.SimpleSerial)
    scope.default_setup()

    cw.program_target(scope, PROG_TYPE, TARGET_BIN_PATH)

    return scope, target


def get_pt(scope: cw.scopes.ScopeTypes, target: cw.targets.TargetTypes, msg: bytearray) -> tuple[bytearray, np.ndarray]:
    scope.arm()

    # 4 bytes
    target.simpleserial_write('p', msg)

    timeout = scope.capture()
    if timeout:
        print("get_pt: mehhh, scope.capture timed out")

    response = target.simpleserial_read('r', GET_PT_RESPONSE_LEN, timeout=2000)
    trace = scope.get_last_trace()

    # idle state should be cut off from the trace
    return response, trace[:2200]


def reset(target: cw.targets.TargetTypes):
    target.simpleserial_write('x', b'')
    _ = target.simpleserial_read('r', RESET_RESPONSE_LEN, timeout=2000)
    return


def check_array(scope: cw.scopes.ScopeTypes, target: cw.targets.TargetTypes, msg: bytearray) -> tuple[bytearray, np.ndarray]:
    scope.arm()

    # 30 bytes
    target.simpleserial_write('a', msg)

    timeout = scope.capture()
    if timeout:
        print("check_array1: mehhh, scope.capture timed out")

    response = target.simpleserial_read('r', FLAG_LEN, timeout=2000) # check flag len
    trace = scope.get_last_trace()

    # idle state should be cut off from the trace
    return response, trace


def num_q(target: cw.targets.TargetTypes):
    target.simpleserial_write('q', b'\x00')
    res = target.simpleserial_read('r', NUM_Q_RESPONSE_LEN, timeout=2000)
    return res


if __name__ == "__main__":
    scope, target = cw_setup()

    result = []

    msg = bytearray([0, 0x00, 0x00, 14])

    for i in range(15):
        pos = 14 - i
        
        low = 0
        high = 0xfffe

        msg[1] = 0x00
        msg[2] = 0x00
        msg[3] = pos
        _ = reset(target)
        _, template = get_pt(scope, target, msg)

        while low <= high:
            mid = (low + high) // 2

            msg[1] = mid & 0xff
            msg[2] = (mid >> 8) & 0xff
            _ = reset(target)
            _, new_trace = get_pt(scope, target, msg)

            distance = np.linalg.norm(template - new_trace)
            if distance > THRESHOLD:
                high = mid - 1
            else:
                low = mid + 1

        result.insert(0, high)
        prev_high = high

    res_unordered = result
    result.sort()
    arr_bytes = bytearray()
    for val in result:
        arr_bytes += val.to_bytes(2, byteorder="little", signed=False)

    flag, _ = check_array(scope, target, arr_bytes)
    queries = num_q(target)

    print(f"Key found: {[hex(x) for x in res_unordered]}")
    print(f"Flag found: {flag}")
    print(f"Number of queries: {int.from_bytes(queries, byteorder='little')}")

