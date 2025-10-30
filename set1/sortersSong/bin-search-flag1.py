import chipwhisperer as cw
import numpy as np
import matplotlib.pyplot as plt
import math

PLATFORM = "CWNANO"
PROG_TYPE = cw.programmers.STM32FProgrammer

# TARGET_BIN_PATH = f"../../targets/sortersSong/sortersSong-{PLATFORM}.hex"
TARGET_BIN_PATH = f"../../../csaw_esc_2025/challenges/set1/sortersSong-CWNANO.hex"

GET_PT_RESPONSE_LEN = 2
SORT_RESPONSE_LEN = 1
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

    target.simpleserial_write('p', msg)

    timeout = scope.capture()
    if timeout:
        print("get_pt: mehhh, scope.capture timed out")

    response = target.simpleserial_read('r', GET_PT_RESPONSE_LEN, timeout=2000)
    trace = scope.get_last_trace()

    # idle state should be cut off from the trace
    return response, trace


def reset(target: cw.targets.TargetTypes):
    target.simpleserial_write('x', b'')
    _ = target.simpleserial_read('r', RESET_RESPONSE_LEN, timeout=2000)
    return


def sort_data1(scope: cw.scopes.ScopeTypes, target: cw.targets.TargetTypes) -> np.ndarray:
    scope.arm()

    target.simpleserial_write('c', b'')

    timeout = scope.capture()
    if timeout:
        print("sort_data1: mehhh, scope.capture timed out")

    _ = target.simpleserial_read('r', SORT_RESPONSE_LEN, timeout=2000)
    trace = scope.get_last_trace()

    # idle state should be cut off from the trace
    return trace[:500]


def check_array1(scope: cw.scopes.ScopeTypes, target: cw.targets.TargetTypes, msg: bytearray) -> tuple[bytearray, np.ndarray]:
    scope.arm()

    # 15 bytes
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

    msg = bytearray([1, 0x00, 0x00, 14])
    prev_high = 0xfe

    # Key lenght is 15 elements (for flag1 = 15 bytes)
    for i in range(15):
        pos = 14 - i
        
        low = 0
        high = prev_high

        msg[1] = 0x00
        msg[3] = pos

        # setting the smallest number at the beginning of array
        # and capturing the trace without shifts for future comparison
        _, _ = get_pt(scope, target, msg)
        no_shift_trace = sort_data1(scope, target)

        num_bits = math.ceil(math.log2(high + 1))
        # binary search
        for _ in range(num_bits):
            mid = (low + high) // 2

            msg[1] = mid
            _, _ = get_pt(scope, target, msg)
            new_trace = sort_data1(scope, target)

            distance = np.linalg.norm(no_shift_trace - new_trace)
            if distance > THRESHOLD:
                high = mid - 1
            else:
                low = mid + 1

        result.insert(0, high)
        # key array is sorted, and our search is moving right-to-left, 
        # so higher bounrady can be decreased (and not set to 0xff by default)
        prev_high = high


    flag, _ = check_array1(scope, target, bytearray(result))
    queries = num_q(target)

    print(f"Key1 found: {[hex(x) for x in result]}")
    print(f"Flag1 found: {flag.decode()}")
    print(f"Number of queries: {int.from_bytes(queries, byteorder='little')}")

