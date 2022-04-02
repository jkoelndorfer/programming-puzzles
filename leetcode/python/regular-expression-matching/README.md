Regular Expression Matching
===========================

Python solution to the Leetcode problem "Regular Expression Matching".

https://leetcode.com/problems/regular-expression-matching/

Commentary
----------

As I started to conceptualize this problem, I first thought about a state
machine implementation, since basic regular expressions are a classic example
of the state machine. This program also smelled a lot to me like it was ripe
for a dynamic programming solution, but I left that alone for the first
go-round.

### State Machine Solution

There are some issues with this approach that center on the glob (`*`)
functionality.

It didn't take very long for me to realize that backtracking would
be necessary. Suppose you are provided a pattern string like
`a*aab` and an input string like `aab`. Clearly a match, yes? Well,
if `a*` is greedy and consumes all the `a` characters from the input
string before the literal `aa` can, your match is hosed.

The second issue I ran into was with an input string like `'aaaaaaaaaaaac'`
and a pattern like `'a*a*a*a*a*a*a*a*a*a*a*a*b'`. The backtracking
functionality of my state machine was creating backtrack checkpoints
at every occurrence of `a*` in a O(n^2) fashion. Obviously very slow.

To mitigate that, I broke the the pattern string up into `MatchAtom`s
and omitted a `MatchAtom` from the list of matchers if it was
redundant. Which is to say, in a pattern like `a*a*`, the second
`a*` is redundant and will not have any impact on the matchability
of the input string. Similarly with a pattern like `.*a*`.

It didn't help much. This state machine solution is pretty slow.
I like state machines because I find them easy to grok. I certainly
think this one is pretty easy to follow.
