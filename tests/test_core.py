import unittest
from fractions import Fraction

from py_stern_brocot_tree import (
    SternBrocotTree,
    Fraction as ExportedFraction,
    mediant,
    farey_sequence,
)


class TestExports(unittest.TestCase):
    def test_fraction_is_the_stdlib_fraction(self):
        # The library re-exports Fraction so callers do not need to import
        # it twice. It must be the same object, not a subclass or wrapper.
        self.assertIs(ExportedFraction, Fraction)


class TestMediant(unittest.TestCase):
    def test_mediant_of_neighbours(self):
        self.assertEqual(mediant(Fraction(0, 1), Fraction(1, 1)), Fraction(1, 2))

    def test_mediant_reduces_through_fraction(self):
        # 1/2 and 2/4 are the same rational; Fraction canonicalises them.
        self.assertEqual(mediant(Fraction(1, 2), Fraction(2, 4)), Fraction(3, 6))

    def test_mediant_of_sentinels_is_root(self):
        # 0/1 and 1/1 give 1/2, but 0/1 and 1/0 give 1/1. The latter is
        # the root of the tree. We cannot pass 1/0 as a Fraction, so we
        # test the pair-based path indirectly through the tree instead.
        tree = SternBrocotTree()
        self.assertEqual(tree.root(), Fraction(1, 1))


class TestAtPath(unittest.TestCase):
    def setUp(self):
        self.tree = SternBrocotTree()

    def test_root_is_one(self):
        self.assertEqual(self.tree.at_path(""), Fraction(1, 1))

    def test_single_left_is_one_half(self):
        self.assertEqual(self.tree.at_path("L"), Fraction(1, 2))

    def test_single_right_is_two(self):
        self.assertEqual(self.tree.at_path("R"), Fraction(2, 1))

    def test_two_moves(self):
        self.assertEqual(self.tree.at_path("LL"), Fraction(1, 3))
        self.assertEqual(self.tree.at_path("LR"), Fraction(2, 3))
        self.assertEqual(self.tree.at_path("RL"), Fraction(3, 2))
        self.assertEqual(self.tree.at_path("RR"), Fraction(3, 1))

    def test_invalid_move_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.tree.at_path("LX")
        self.assertIn("invalid move", str(ctx.exception))

    def test_empty_path_does_not_raise(self):
        self.assertEqual(self.tree.at_path(""), Fraction(1, 1))


class TestInOrder(unittest.TestCase):
    def setUp(self):
        self.tree = SternBrocotTree()

    def test_depth_zero_is_just_root(self):
        self.assertEqual(list(self.tree.in_order(0)), [Fraction(1, 1)])

    def test_depth_one_is_sorted(self):
        # In-order at depth 1 yields 1/2, 1/1, 2/1.
        self.assertEqual(
            list(self.tree.in_order(1)),
            [Fraction(1, 2), Fraction(1, 1), Fraction(2, 1)],
        )

    def test_depth_two_is_sorted(self):
        # Full in-order walk to depth 2: 1/3, 1/2, 2/3, 1/1, 3/2, 2/1, 3/1.
        self.assertEqual(
            list(self.tree.in_order(2)),
            [
                Fraction(1, 3),
                Fraction(1, 2),
                Fraction(2, 3),
                Fraction(1, 1),
                Fraction(3, 2),
                Fraction(2, 1),
                Fraction(3, 1),
            ],
        )

    def test_in_order_is_strictly_increasing(self):
        values = list(self.tree.in_order(4))
        for a, b in zip(values, values[1:]):
            self.assertLess(a, b)

    def test_negative_depth_raises(self):
        with self.assertRaises(ValueError):
            list(self.tree.in_order(-1))

    def test_depth_is_a_bound_not_a_filter(self):
        # Every node at depth <= max_depth must appear. A depth-1 node
        # must be present in the depth-2 walk.
        shallow = set(self.tree.in_order(1))
        deep = set(self.tree.in_order(2))
        self.assertTrue(shallow.issubset(deep))


class TestFind(unittest.TestCase):
    def setUp(self):
        self.tree = SternBrocotTree()

    def test_find_root(self):
        self.assertEqual(self.tree.find(Fraction(1, 1)), "")

    def test_find_simple_paths(self):
        self.assertEqual(self.tree.find(Fraction(1, 2)), "L")
        self.assertEqual(self.tree.find(Fraction(2, 1)), "R")
        self.assertEqual(self.tree.find(Fraction(1, 3)), "LL")
        self.assertEqual(self.tree.find(Fraction(2, 3)), "LR")
        self.assertEqual(self.tree.find(Fraction(3, 2)), "RL")
        self.assertEqual(self.tree.find(Fraction(3, 1)), "RR")

    def test_find_round_trips_with_at_path(self):
        for path in ["", "L", "R", "LL", "LR", "RL", "RR", "LLL", "LLR", "LRR"]:
            value = self.tree.at_path(path)
            self.assertEqual(self.tree.find(value), path)

    def test_find_rejects_non_positive(self):
        with self.assertRaises(ValueError):
            self.tree.find(Fraction(0, 1))
        with self.assertRaises(ValueError):
            self.tree.find(Fraction(-1, 2))

    def test_find_rejects_non_fraction(self):
        with self.assertRaises(TypeError):
            self.tree.find(1)  # type: ignore[arg-type]

    def test_find_fraction_with_large_terms(self):
        # 355/113 is a well-known convergent of pi. It is in lowest terms
        # and positive, so the descent must reach it.
        value = Fraction(355, 113)
        path = self.tree.find(value)
        self.assertEqual(self.tree.at_path(path), value)


class TestFareySequence(unittest.TestCase):
    def test_f0_is_empty(self):
        self.assertEqual(farey_sequence(0), [])

    def test_f1(self):
        self.assertEqual(farey_sequence(1), [Fraction(0, 1), Fraction(1, 1)])

    def test_f2(self):
        self.assertEqual(
            farey_sequence(2),
            [Fraction(0, 1), Fraction(1, 2), Fraction(1, 1)],
        )

    def test_f5_matches_known_sequence(self):
        self.assertEqual(
            farey_sequence(5),
            [
                Fraction(0, 1),
                Fraction(1, 5),
                Fraction(1, 4),
                Fraction(1, 3),
                Fraction(2, 5),
                Fraction(1, 2),
                Fraction(3, 5),
                Fraction(2, 3),
                Fraction(3, 4),
                Fraction(4, 5),
                Fraction(1, 1),
            ],
        )

    def test_farey_is_sorted_and_unique(self):
        seq = farey_sequence(10)
        self.assertEqual(len(seq), len(set(seq)))
        for a, b in zip(seq, seq[1:]):
            self.assertLess(a, b)

    def test_negative_n_raises(self):
        with self.assertRaises(ValueError):
            farey_sequence(-1)

    def test_non_int_n_raises(self):
        with self.assertRaises(TypeError):
            farey_sequence(2.0)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
