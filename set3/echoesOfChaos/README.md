# Solution

Key found: `['0x2b9', '0x1988', '0x2384', '0x369f', '0x4ca1', '0x6582', '0x6d3c', '0x73a0', '0x8cf0', '0xa56d', '0xb3ac', '0xc034', '0xe594', '0xfcec', '0xfdda']`

Flag found: `eoc{th3yreC00ked}   `

Number of queries: 256

# Approach

This target is similar to *Sorters Song* (set 1, challenge 2), and our approach is almost the same as in that challenge. 

The target internally uses merge sort, and the original key is kept unsorted.
Our code captures the power trace of the sorting operation, but since merge sort can generate traces that are lenghty to capture in full on the CWNANO, we only analyze the first comparison of the leftmost two elements.

First, we insert the smallest possible value (`0x0000`) and capture its trace. This trace represents the case with no shift operations, and we use it as a reference for comparison.

Next, we perform a binary search to find each element of the key:

* For each guessed value, we capture a new sorting trace for the first left comparison.
* We compare it to the reference trace using the Euclidean distance (`numpy.linalg.norm` in Python).
* Based on the distance, we decide whether to adjust the lower or upper bound of the search range.

We repeat this process for all 15 key values. Each comparison involves `reset()` (which does not icrement the number of queries) and `get_pt()`, which returns traces of sorting (and increments the number of queries)

The maximum number of queries for a 15-element (16-bit per value) key is:
* 15 values
* multiplied by 1 query per comparison
* multiplied by 16 iterations per binary search (`log2(2^16)`)
* plus 1 reference query per value

= 255 in total. Plus, one query for `check_array()`

Our implementation recovered the flag `eoc{th3yreC00ked}   ` in exactly 256 queries.




#######

Apparently, the code it's not stable enough and can require a couple of re-runs, see:
```
krogova:echoesOfChaos$ python3 echoesOfChaos.py 
Detected known STMF32: STM32F04xxx
Extended erase (0x44), this can take ten seconds or more
Attempting to program 14307 bytes at 0x8000000
STM32F Programming flash...
STM32F Reading flash...
Verified flash OK, 14307 bytes
Key found: ['0x2b9', '0x1988', '0x2384', '0x369f', '0x4ca1', '0x4ca1', '0x6582', '0x6d3c', '0x73a0', '0x8cf0', '0xa56d', '0xb3ac', '0xe594', '0xfcec', '0xfdda']
Flag found: bytearray(b'q3L!x9bX2f@mV#6dWrx\n')
Number of queries: 256

krogova:echoesOfChaos$ python3 echoesOfChaos.py 
Detected known STMF32: STM32F04xxx
Extended erase (0x44), this can take ten seconds or more
Attempting to program 14307 bytes at 0x8000000
STM32F Programming flash...
STM32F Reading flash...
Verified flash OK, 14307 bytes
Key found: ['0x2b9', '0x1988', '0x2384', '0x369f', '0x4ca1', '0x6582', '0x6d3c', '0x73a0', '0x8cf0', '0xa56d', '0xb3ac', '0xc034', '0xe594', '0xfcec', '0xfdda']
Flag found: bytearray(b'eoc{th3yreC00ked}   ')
Number of queries: 256
```