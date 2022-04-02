#!/usr/bin/env python3

from enum import auto, Enum
import logging
from typing import List
import sys


def configure_logging():
    logger = logging.getLogger("regexmatch")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())


class _MatchState(Enum):
    DETERMINE_NEXT_MATCH = auto()
    MATCH_ATOM = auto()
    MATCH_SUCCESS = auto()
    MATCH_FAIL_ATTEMPT_BACKTRACK = auto()
    MATCH_FAIL_FINAL = auto()


class MatchAtomType(Enum):
    MATCH_SINGLE_CHARACTER = auto()
    MATCH_ZERO_OR_MORE_CHARACTERS = auto()


class MatchAtom:
    """
    Object representing a match atom. An atom is the smallest part
    of a pattern string that represents something which can be matched.

    The following pattern strings describe valid match atoms:
        "a"
        "a*"
        "."
        ".*"

    The following pattern strings are NOT valid match atoms:
        "aa" (this can be further reduced)
        "*"  (* indicates zero or more, but of what?)
    """

    ANY_CHARACTER = "ANY"

    def __init__(self, c: str, match_type: MatchAtomType) -> None:
        if c != self.ANY_CHARACTER and len(c) > 1:
            raise ValueError("expected len(c) == 0 or len(c) == 1")
        self.c = c
        self.match_type = match_type

    def matches(self, c: str) -> bool:
        """
        Given an input char c, returns True if c matches this MatchAtom.
        """
        if len(c) > 1:
            raise ValueError("expected len(c) == 0 or len(c) == 1")

        if len(c) == 0 and self.match_type == MatchAtomType.MATCH_ZERO_OR_MORE_CHARACTERS:
            return True
        elif len(c) == 1 and (self.c == c or self.c == self.ANY_CHARACTER):
            return True

        return False

    def redundant_with_subsequent(self, subsequent: "MatchAtom") -> bool:
        """
        Determines whether a MatchAtom immediately following this one would be
        redundant. Helps simplify patterns like 'a*a*a*a*' which would otherwise
        create a large number of useless BacktrackStates.
        """
        if (
            (self.c == subsequent.c or self.c == self.ANY_CHARACTER)
            and self.match_type == MatchAtomType.MATCH_ZERO_OR_MORE_CHARACTERS
            and subsequent.match_type == MatchAtomType.MATCH_ZERO_OR_MORE_CHARACTERS
        ):
            return True

        return False

    def __repr__(self) -> str:
        if self.match_type == MatchAtomType.MATCH_SINGLE_CHARACTER:
            return self.c
        elif self.match_type == MatchAtomType.MATCH_ZERO_OR_MORE_CHARACTERS:
            return f"{self.c}*"
        else:
            raise ValueError(f"don't know how to display MatchAtomType {self.match_type}")


class BacktrackState:
    """
    Contains backtracking information.

    Backtracking is used to unwind glob matching ('*'). By default, glob
    operates greedily, consuming as many characters as it can.

    Given a pattern string "abc*cdef" and input string "abcdef", the
    "c*" part of the pattern will consume the input string's "c". Because
    the literal "c" in the pattern has no "c" to consume, the match
    will fail.

    We need to be able to roll back to any point within a zero-or-more
    character match and continue matching until we have run out of backtrack
    states.
    """

    def __init__(self, s_idx: int, match_atom_idx: int) -> None:
        self.s_idx = s_idx
        self.match_atom_idx = match_atom_idx


class MatchState:
    def __init__(self, s: str, match_atoms: List[MatchAtom]) -> None:
        # Current state of the regular expression state machine.
        #
        # As we walk through the pattern and match string, this
        # value will change to reflect the current task.
        self.state = _MatchState.MATCH_ATOM

        # Input string (i.e. string to match against).
        self.s = s

        # Current position in input string.
        self.s_idx = 0

        # List of match atoms against which to test the input string.
        #
        # Match atoms are derived from the pattern string.
        self.match_atoms = match_atoms

        # Current position in the list of match atoms.
        self.match_atom_idx = 0

        # List of states we can backtrack to in case of a match failure
        # in a pattern containing zero-or-more-character matches.
        self.backtracks: List[BacktrackState] = list()

    def create_backtrack(self) -> None:
        if self.match_atom_idx >= len(self.match_atoms) - 1:
            # No atoms follow the one we are currently processing, so
            # setting a backtrack doesn't make sense. Skip it.
            return
        self.backtracks.append(BacktrackState(self.s_idx, self.match_atom_idx + 1))

    @property
    def match_atom(self) -> MatchAtom:
        return self.match_atoms[self.match_atom_idx]


class Solution:
    STATE_TRANSITION_EXC = Exception("don't know how to transition to new state")

    def __init__(self) -> None:
        self.log = logging.getLogger(f"regexmatch.{self.__class__.__name__}")

    def atomize_pattern(self, p: str) -> List[MatchAtom]:
        """
        Converts a pattern string into a list of MatchAtoms.
        """
        match_atoms = list()
        last_match_atom = None
        i = 0
        while i < len(p):
            # The character that the atom will match against.
            match_char = p[i]

            if match_char == ".":
                match_char = MatchAtom.ANY_CHARACTER

            i += 1
            # The type of match to perform. If this is a "*", we match
            # match_char zero or more times. Otherwise, match a single
            # character.
            try:
                match_type_s = p[i]
            except IndexError:
                match_type_s = ""

            if match_type_s == "*":
                match_type = MatchAtomType.MATCH_ZERO_OR_MORE_CHARACTERS
                i += 1
            else:
                match_type = MatchAtomType.MATCH_SINGLE_CHARACTER

            match_atom = MatchAtom(match_char, match_type)

            # If the last match atom we created is redundant with the new one,
            # don't bother adding the new one to the list.
            if last_match_atom is not None and last_match_atom.redundant_with_subsequent(match_atom):
                continue

            match_atoms.append(match_atom)
            last_match_atom = match_atom

        return match_atoms

    def log_state(self, state: _MatchState, match_state: MatchState) -> None:
        s = match_state
        self.log.debug(f"state = {state.name}; s_idx = {s.s_idx}; match_atom_idx = {s.match_atom_idx}")

    def determine_next_match(self, match_state: MatchState) -> None:
        """
        Determines the next match to make (or if we are finished).
        """
        self.log_state(_MatchState.DETERMINE_NEXT_MATCH, match_state)
        match_state.match_atom_idx += 1

        if match_state.match_atom_idx >= len(match_state.match_atoms):
            # We've finished stepping through the list of match atoms. If all of the
            # input string has been consumed, we have a match. If we don't, it's only
            # a partial match. Partial matches are non-matches.
            if match_state.s_idx >= len(match_state.s):
                match_state.state = _MatchState.MATCH_SUCCESS
            else:
                match_state.state = _MatchState.MATCH_FAIL_ATTEMPT_BACKTRACK
            return

        match_state.state = _MatchState.MATCH_ATOM

    def match_atom(self, match_state: MatchState) -> None:
        self.log_state(_MatchState.MATCH_ATOM, match_state)
        try:
            input_char = match_state.s[match_state.s_idx]
        except IndexError:
            input_char = ""

        if match_state.match_atom.matches(input_char):
            self.handle_match_atom_success(input_char, match_state)
        else:
            self.handle_match_atom_fail(input_char, match_state)

    def handle_match_atom_success(self, input_char: str, match_state: MatchState) -> None:
        ma = match_state.match_atom
        self.log.debug(f"atom '{ma}' matches input char '{input_char}'")

        if ma.match_type == MatchAtomType.MATCH_SINGLE_CHARACTER:
            match_state.state = _MatchState.DETERMINE_NEXT_MATCH
        elif ma.match_type == MatchAtomType.MATCH_ZERO_OR_MORE_CHARACTERS:
            if len(input_char) > 0:
                match_state.create_backtrack()

                # This is is logically a no-op. It is here for clarity.
                match_state.state = _MatchState.MATCH_ATOM
            else:
                # If there is no input_char, we've reached the end of the input string.
                # Don't create a backtrack for that. Instead, DETERMINE_NEXT_MATCH
                # should examine the pattern and input string to see if the match
                # is good.
                match_state.state = _MatchState.DETERMINE_NEXT_MATCH
        else:
            raise self.STATE_TRANSITION_EXC

        match_state.s_idx += 1

    def handle_match_atom_fail(self, input_char: str, match_state: MatchState) -> None:
        ma = match_state.match_atom
        self.log.debug(f"atom '{ma}' DOES NOT MATCH input char '{input_char}'")
        if ma.match_type == MatchAtomType.MATCH_SINGLE_CHARACTER:
            match_state.state = _MatchState.MATCH_FAIL_ATTEMPT_BACKTRACK
        elif ma.match_type == MatchAtomType.MATCH_ZERO_OR_MORE_CHARACTERS:
            match_state.state = _MatchState.DETERMINE_NEXT_MATCH
        else:
            raise self.STATE_TRANSITION_EXC

    def match_fail_attempt_backtrack(self, match_state: MatchState) -> None:
        self.log_state(_MatchState.MATCH_FAIL_ATTEMPT_BACKTRACK, match_state)
        if len(match_state.backtracks) == 0:
            match_state.state = _MatchState.MATCH_FAIL_FINAL
        else:
            backtrack = match_state.backtracks.pop()
            match_state.state = _MatchState.MATCH_ATOM
            match_state.s_idx = backtrack.s_idx
            match_state.match_atom_idx = backtrack.match_atom_idx

    def isMatch(self, s: str, p: str) -> bool:
        match_atoms = self.atomize_pattern(p)
        match_state = MatchState(s, match_atoms)

        while match_state.state not in (_MatchState.MATCH_SUCCESS, _MatchState.MATCH_FAIL_FINAL):
            st = match_state.state
            if st == _MatchState.DETERMINE_NEXT_MATCH:
                self.determine_next_match(match_state)
            elif st == _MatchState.MATCH_ATOM:
                self.match_atom(match_state)
            elif st == _MatchState.MATCH_FAIL_ATTEMPT_BACKTRACK:
                self.match_fail_attempt_backtrack(match_state)

        return match_state.state == _MatchState.MATCH_SUCCESS


if __name__ == "__main__":
    configure_logging()
    sln = Solution()
    input_string = sys.argv[1]
    pattern = sys.argv[2]
    if sln.isMatch(input_string, pattern):
        print(f"input string '{input_string}' matches pattern '{pattern}'", file=sys.stderr)
    else:
        print(f"input string '{input_string}' DOES NOT MATCH pattern '{pattern}'", file=sys.stderr)

    # Leetcode seems to not like when we exit with a nonzero code, so we
    # don't exit with a proper code.
