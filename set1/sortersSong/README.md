# Solution

## Flag 1

Key1 found: `['0x7', '0xc', '0x2b', '0x34', '0x39', '0x42', '0x50', '0x68', '0x71', '0x7c', '0x88', '0x93', '0xac', '0xb1', '0xdb']`

Flag1 found: `ss1{y0u_g0t_it_br0!}`

Number of queries: 241

## Flag 2

Key2 found: `['0x366', '0x248a', '0x4022', '0x4901', '0x4be1', '0x695c', '0x709c', '0x8789', '0x9087', '0x94f6', '0x9a72', '0xa63a', '0xb365', '0xc916', '0xd4db']`

Flag2 found: `ss2{!AEGILOPS_chimps`

Number of queries: 497

# Approach


The target internally uses insertion sort.
Our code captures the power trace of the sorting operation when inserting one new element into the beginning of the existing sorted array. By analyzing these traces, we can recover the exact values of the initial array.

First, we insert the smallest possible value (`0x00`) and capture its trace. This trace represents the case with no shift operations, and we use it as a reference for comparison.

Next, we perform a binary search to find each element of the key:

* For each guessed value, we capture a new sorting trace.
* We compare it to the reference trace using the Euclidean distance (Function `numpy.linalg.norm` in Python).
* Based on the distance, we decide whether to adjust the lower or upper bound of the search range.

We repeat this process for all 15 key bytes, starting from the highest index (rightmost element).
Each comparison involves two queries:
1. `get_pt` — to set the guessed value, and
2. `sort_data1` — to capture the corresponding trace.

The maximum number of queries for a 15-byte (8-bit per value) key is:
* 15 values
* multiplied by 2 queries per comparison
* multiplied by 8 iterations per binary search (`log₂(2⁸)`)
* plus 2 reference queries per value

= 270 queries in total.
For 16-bit values, this number is roughly doubled.

Our implementation recovered the first flag `ss1{y0u_g0t_it_br0!}` in 241 queries, and the second flag `ss2{!AEGILOPS_chimps` in 497 queries. 
