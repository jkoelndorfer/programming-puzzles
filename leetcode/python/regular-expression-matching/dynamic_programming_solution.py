#!/usr/bin/env python3

import sys


class Solution:
    def isMatch(self, s: str, p: str) -> bool:
        dp_memo = [([None] * (len(p) + 1)) for _ in range(len(s) + 1)]
        return self.match(dp_memo, s, 0, p, 0)

    def match(self, dp_memo, s: str, s_idx: int, p: str, p_idx: int) -> bool:
        if p_idx >= len(p):
            return s_idx >= len(s)

        # matched is True is the current part of the pattern string
        # matches the current part of the input string.
        matched = False
        if s_idx < len(s):
            memo = dp_memo[s_idx][p_idx]
            if memo is not None:
                return memo

            sc = s[s_idx]
            pc = p[p_idx]
            if sc == pc or pc == ".":
                matched = True

        if p_idx + 1 < len(p) and p[p_idx + 1] == "*":
            # The current pattern atom is a glob.
            single_match = False
            unglobbed = self.match(dp_memo, s, s_idx, p, p_idx + 2)
            globbed = matched and self.match(dp_memo, s, s_idx + 1, p, p_idx)
        else:
            # The current pattern atom is a single character.
            single_match = matched and self.match(dp_memo, s, s_idx + 1, p, p_idx + 1)
            globbed = False
            unglobbed = False

        result = single_match or globbed or unglobbed
        dp_memo[s_idx][p_idx] = result
        return result


if __name__ == "__main__":
    sln = Solution()

    s = sys.argv[1]
    if s == "test_cases":
        assert not sln.isMatch("aa", "a")
        assert sln.isMatch("aa", "a*")
        assert not sln.isMatch("mississippi", "mis*is*p*.")
        assert sln.isMatch("aab", "c*a*b*")
        assert sln.isMatch("a", "ab*")
        assert sln.isMatch("aaaaaaaaaaaaab", "a*a*a*a*a*a*a*a*a*a*a*a*b")
        assert not sln.isMatch("aaaaaaaaaaaaac", "a*a*a*a*a*a*a*a*a*a*a*a*b")
    else:
        p = sys.argv[2]
        print(Solution().isMatch(s, p))
