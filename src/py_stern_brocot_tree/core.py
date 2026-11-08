"""Stern-Brocot tree: ordered rational retrieval without floating point.

The tree is never materialised. Every node is addressed by a pair of
bounding fractions (left, right) plus a depth, and the path to a node is
kept as a short string of 'L'/'R' moves. This keeps memory bounded and
makes the ordering property explicit: an in-order walk of the tree yields
the Stern-Brocot sequence, which is exactly the rationals in lowest terms,
in increasing order.

Fractions are represented with :class:`fractions.Fraction` from the
standard library. That choice costs a little speed versus a hand-rolled
integer pair, but it gives canonical lowest-terms reduction and exact
comparison for free, which is the whole point of the library.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Iterator, List, Tuple

__all__ = [
    "SternBrocotTree",
    "Fraction",
    "mediant",
    "farey_sequence",
]


# Left and right sentinels. 0/1 and 1/0 bracket the positive rationals.
# 1/0 is not a Fraction, so it is stored as a (numerator, denominator)
# pair internally and only converted when a real value is needed.
_LEFT = (0, 1)
_RIGHT = (1, 0)


def mediant(a: Fraction, b: Fraction) -> Fraction:
    """Return the mediant of two fractions.

    The mediant (a.num + b.num) / (a.den + b.den) is the operation that
generates the Stern-Brocot tree. It is deliberately not reduced here:
callers that need a canonical value should let :class:`Fraction` do it,
but keeping the raw sum visible makes the tree structure clearer.
    """
    return Fraction(a.numerator + b.numerator, a.denominator + b.denominator)


def _mediant_pair(a: Tuple[int, int], b: Tuple[int, int]) -> Tuple[int, int]:
    """Mediant of two (num, den) pairs, without constructing a Fraction.

    Used internally so that the 1/0 sentinel can participate without
    raising ZeroDivisionError.
    """
    return (a[0] + b[0], a[1] + b[1])


def _to_fraction(pair: Tuple[int, int]) -> Fraction:
    """Convert a (num, den) pair to a Fraction.

    The 1/0 sentinel is not representable as a Fraction; callers must
    avoid asking for it. We raise a clear error rather than letting the
    stdlib raise ZeroDivisionError, because the sentinel is an internal
    convention and the message should say so.
    """
    num, den = pair
    if den == 0:
        raise ZeroDivisionError(
            "the 1/0 sentinel is not a rational number; "
            "it only exists to bound the positive side of the tree"
        )
    return Fraction(num, den)


class SternBrocotTree:
    """An implicitly represented Stern-Brocot tree of positive rationals.

    The tree is infinite, so it is never built. Instead, nodes are
    addressed by a path of 'L' and 'R' moves from the root. The root is
    the mediant of the sentinels 0/1 and 1/0, which is 1/1.

    Two operations matter for retrieval:

    * :meth:`at_path` returns the fraction at a given path.
    * :meth:`in_order` yields fractions in increasing order, breadth-first
      by depth, which is the property that makes the tree useful as an
      ordered rational generator.

    The tree contains every positive rational exactly once, in lowest
    terms. Negative rationals and zero are not represented; that is a
    deliberate scope decision, because the Stern-Brocot construction is
    naturally a positive-rational construction and extending it would
    complicate the sentinel logic without adding anything to the ordered
    retrieval use case.
    """

    def __init__(self) -> None:
        self._left = _LEFT
        self._right = _RIGHT

    def root(self) -> Fraction:
        """Return the root of the tree, 1/1."""
        return Fraction(1, 1)

    def at_path(self, path: str) -> Fraction:
        """Return the fraction reached by following ``path`` from the root.

        ``path`` is a string of 'L' and 'R' characters. The empty string
        is the root. Any other character raises :class:`ValueError`.

        The walk keeps the two bounding fractions and takes the mediant
        at each step, which is O(len(path)) time and O(1) memory.
        """
        left = self._left
        right = self._right
        for i, move in enumerate(path):
            if move == "L":
                right = _mediant_pair(left, right)
            elif move == "R":
                left = _mediant_pair(left, right)
            else:
                raise ValueError(
                    f"invalid move {move!r} at index {i}; expected 'L' or 'R'"
                )
        return _to_fraction(_mediant_pair(left, right))

    def in_order(self, max_depth: int = 10) -> Iterator[Fraction]:
        """Yield fractions in increasing order up to ``max_depth``.

        The traversal is an explicit depth-first in-order walk of the
        implicit tree. An explicit stack is used rather than recursion so
        that ``max_depth`` can be large without hitting the interpreter's
        recursion limit.

        ``max_depth`` is the maximum number of moves from the root. A
        depth of 0 yields only the root. Negative depths raise
        :class:`ValueError`.
        """
        if max_depth < 0:
            raise ValueError("max_depth must be non-negative")
        if max_depth == 0:
            yield self.root()
            return

        # Stack entries are (left, right, depth, visited). The 'visited'
        # flag distinguishes the two visits to a node in an in-order walk:
        # first we descend left, then we emit the node, then we descend
        # right. This avoids a second stack for the right subtree.
        stack: List[Tuple[Tuple[int, int], Tuple[int, int], int, bool]] = [
            (self._left, self._right, 0, False)
        ]
        while stack:
            left, right, depth, visited = stack.pop()
            if visited:
                yield _to_fraction(_mediant_pair(left, right))
                continue
            if depth >= max_depth:
                # At the frontier we still emit the node, but do not
                # descend further. Pushing it again with visited=True is
                # cheaper than special-casing the emit here.
                stack.append((left, right, depth, True))
                continue
            mid = _mediant_pair(left, right)
            # Push right subtree, then node, then left subtree so that
            # popping yields left, node, right -- in-order.
            stack.append((mid, right, depth + 1, False))
            stack.append((left, right, depth, True))
            stack.append((left, mid, depth + 1, False))

    def find(self, value: Fraction) -> str:
        """Return the path to ``value``, or raise :class:`ValueError`.

        The search is the standard Stern-Brocot descent: compare the
        target against the current mediant and move left or right. It is
        O(log(max(num, den))) moves for a rational in lowest terms, which
        is the reason the tree is interesting as a retrieval structure.

        Only positive rationals are represented. ``value`` must be a
        :class:`fractions.Fraction`; integers and floats are rejected so
        that callers do not silently get a different type's semantics.
        """
        if not isinstance(value, Fraction):
            raise TypeError("value must be a fractions.Fraction")
        if value <= 0:
            raise ValueError("only positive rationals are represented")

        left = self._left
        right = self._right
        path_chars: List[str] = []
        # The descent terminates because the Stern-Brocot tree contains
        # every positive rational in lowest terms exactly once, and the
        # bounding interval shrinks strictly at each step. A generous
        # guard keeps a corrupted invariant from looping forever.
        for _ in range(10_000):
            mid = _mediant_pair(left, right)
            mid_fraction = Fraction(mid[0], mid[1])
            if mid_fraction == value:
                return "".join(path_chars)
            if value < mid_fraction:
                right = mid
                path_chars.append("L")
            else:
                left = mid
                path_chars.append("R")
        raise RuntimeError("Stern-Brocot descent did not terminate")


def farey_sequence(n: int) -> List[Fraction]:
    """Return the Farey sequence of order ``n`` as a list of Fractions.

    The Farey sequence F_n is the sorted list of fractions in [0, 1]
    whose denominator is at most n. It is included here because it is the
    finite truncation of the Stern-Brocot tree's in-order walk, and it is
    a convenient way to sanity-check ordering without materialising the
    tree.

    ``n`` must be a non-negative integer. F_0 is empty; F_1 is [0/1, 1/1].
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an int")
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return []

    # The classic Farey recurrence: given consecutive a/b and c/d in F_n,
    # the next denominator is k = (n + b) // d, and the next fraction is
    # (k*c - a) / (k*d - b). This is O(len(F_n)) rather than O(n^2 log n)
    # for a naive scan, and it avoids floating point entirely.
    result: List[Fraction] = [Fraction(0, 1)]
    a, b = 0, 1
    c, d = 1, n
    while True:
        result.append(Fraction(c, d))
        if c == 1 and d == 1:
            break
        k = (n + b) // d
        a, b, c, d = c, d, k * c - a, k * d - b
    return result
