#!/usr/bin/env python3

import sys

sym_value = {
    "IV": 4,
    "IX": 9,
    "XL": 40,
    "XC": 90,
    "CD": 400,
    "CM": 900,
    "I": 1,
    "V": 5,
    "X": 10,
    "L": 50,
    "C": 100,
    "D": 500,
    "M": 1000,
}


class Solution:
    def romanToInt(self, s: str) -> int:
        i = 0
        sum = 0
        while i < len(s):
            twosym_val = sym_value.get(s[i : i + 2], None)
            if twosym_val is not None:
                sum += twosym_val
                i += 2
            else:
                sum += sym_value.get(s[i], 0)
                i += 1
        return sum


if __name__ == "__main__":
    print(Solution().romanToInt(sys.argv[1]))
