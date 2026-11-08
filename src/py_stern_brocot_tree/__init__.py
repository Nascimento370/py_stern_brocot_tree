"""Public API for py_stern_brocot_tree.

Only a small, deliberate surface is exported. The tree is represented
implicitly rather than as a materialised node graph, because the
Stern-Brocot tree is infinite and the useful operations are all
navigational.
"""

from .core import SternBrocotTree, Fraction, mediant, farey_sequence

__all__ = [
    "SternBrocotTree",
    "Fraction",
    "mediant",
    "farey_sequence",
]
