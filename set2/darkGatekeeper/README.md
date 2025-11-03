# Solution

# Euclidean distance

Flag found: `ESC{J0lt_Th3_G473}`

Key found:  `7N4>qp14c70!`

stats:
         Number of queries: 291
         Euclidean distance threshold: 0.7

# Peaks

Flag found: `ESC{J0lt_Th3_G473}`

Key found:  `7N4>qp14c70!`

stats:
    Number of queries: 83
    Peaks height: 0.16

# Approach


The target checks a 12-character master key. The code leaks information about symbol-by-symbol comparison of the guessed key and secret key. When symbols are equal, power trace shows a longer trace (with one more sample) for such branch execution. One possible explanation is that branch prediction fails on that moment and it's detectable on the power trace. 
Our code captures a power trace for each attempted key. We start from an initial guess of `\x00 * 12` and use that initial trace as the reference for comparisons.


## Euclidean distance

1. Keep `trace_with_most_correct_guesses` as the trace corresponding to the longest prefix of the key guessed so far.
2. Iterate positions `i` from left to right (12 characters). For each position, iterate over every ascii character:
   * Build guess by replacing `key[i]` with the ascii character.
   * Send the new quess and obtain a new trace.
   * Compute the Euclidean distance.
   * If the distance exceeds a threshold, treat the candidate as correct for position `i`

Each tested symbol requires one `send()` (one query). The maximum number of queries is `12 * 94 = 1128`, where 12 is number of symbol in the key and 94 is number of ascii characters what we check (We used `string.digits + string.ascii_letters + string.punctuation` from Python standart module)

Our implementation recovered the key `7N4>qp14c70!` (with the flag `ESC{J0lt_Th3_G473}`) in 291 queries.


## Peak-position analysis

1. Capture the reference trace for `\x00 * 12`. Detect peaks in the reference trace (using `scipy.signal.find_peaks`). These peaks represents incorrect guesses for every character in the key. 
2. For each ascii character, send a message of `guessed_char * 12`, capture trace, detect peaks.
3. Compute per-peak index differences between the reference (incorrect) peaks and the current peaks.
4. Any change in the delta pattern indicates which positions became correct for that symbol; update all those positions in `key` at once.
5. Continue iterating symbols until all 12 positions are filled or the device accepts the full key.

The peaks approach can recover multiple positions from a single candidate symbol because correct characters shift peak positions in predictable ways. This makes it far more query-efficient than the per-position Euclidean search. The maximum number of queries is 94 (number of ascii characters what we check). Our implementation is was able to recover the key `7N4>qp14c70!` in 83 queries.

Note: The peak detection threshold needs to be set through testing. Reconnecting the CWNANO/re-uploading the firmware can change the absolute power values, even if the overall pattern stays the same. Currently, the threshold may need to be adjusted manually for each run. With a bit more time for implementation, this could be automated to adjust automatically to changes in the trace.