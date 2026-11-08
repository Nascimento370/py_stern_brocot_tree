# py_stern_brocot_tree

Represents fractions via the Stern-Brocot sequence for ordered rational retrieval.

```python
from fractions import Fraction
from py_stern_brocot_tree import SternBrocotTree, farey_sequence

tree = SternBrocotTree()

# Navigate by path: 'L' goes toward 0/1, 'R' goes toward 1/0.
tree.at_path("")        # Fraction(1, 1)
tree.at_path("L")       # Fraction(1, 2)
tree.at_path("LR")      # Fraction(2, 3)

# Walk the tree in increasing order, up to a depth.
list(tree.in_order(2))
# [Fraction(1, 3), Fraction(1, 2), Fraction(2, 3),
#  Fraction(1, 1), Fraction(3, 2), Fraction(2, 1), Fraction(3, 1)]

# Find the path to a rational. The descent is logarithmic in the terms.
tree.find(Fraction(355, 113))

# Finite truncation of the same ordering.
farey_sequence(5)
# [Fraction(0, 1), Fraction(1, 5), Fraction(1, 4), Fraction(1, 3),
#  Fraction(2, 5), Fraction(1, 2), Fraction(3, 5), Fraction(2, 3),
#  Fraction(3, 4), Fraction(4, 5), Fraction(1, 1)]
```

## Why this exists

The Stern-Brocot tree is the cleanest way to enumerate the positive
rationals in increasing order without duplicates. A naive generator has to
reduce every candidate and keep a set of what it has seen; the tree gives
lowest terms and ordering for free, because the mediant of two neighbours
is always in lowest terms when the neighbours are.

The trade-off is that the tree is infinite and is not materialised here.
Nodes are addressed by a path of `'L'` and `'R'` moves from the root, and
the in-order walk is bounded by a depth. That keeps memory flat and makes
the ordering property explicit, at the cost of not being able to ask for
"the n-th rational" directly without walking. If you need indexed access,
`farey_sequence(n)` gives you a finite sorted list instead.

## The awkward edge

`1/0` is not a rational number, so it cannot be a `Fraction`. It is used
internally as the right-hand sentinel that bounds the positive side of the
tree, and it is never returned. `at_path` and `find` only ever yield
positive rationals; `find` rejects zero and negatives with `ValueError`,
and rejects non-`Fraction` arguments with `TypeError`. The empty path is
the root, `1/1`.

## API

- `SternBrocotTree()` — implicit tree over the positive rationals.
  - `root() -> Fraction` — the root, `1/1`.
  - `at_path(path: str) -> Fraction` — follow `'L'`/`'R'` moves; empty
    string is the root; any other character raises `ValueError`.
  - `in_order(max_depth: int = 10) -> Iterator[Fraction]` — increasing
    order up to `max_depth` moves from the root; negative depth raises
    `ValueError`.
  - `find(value: Fraction) -> str` — path to `value`; raises `ValueError`
    for non-positive values and `TypeError` for non-`Fraction` values.
- `mediant(a: Fraction, b: Fraction) -> Fraction` — `(a.num + b.num) /
  (a.den + b.den)`, the tree's generating operation.
- `farey_sequence(n: int) -> list[Fraction]` — sorted fractions in `[0, 1]`
  with denominator at most `n`; `n` must be a non-negative `int`.
- `Fraction` — re-exported from `fractions` for convenience.
