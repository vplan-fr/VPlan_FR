import unittest
from ..blocks import BlockConfiguration


class TestBlockConfiguration(unittest.TestCase):
    def test_empty_block_configuration(self):
        empty = BlockConfiguration({})

        self.assertEqual(empty.get_periods_of_block(0), [0])
        self.assertEqual(empty.get_periods_of_block(5), [5])
        self.assertEqual(empty.get_periods_of_block(-1), [-1])
        self.assertEqual(empty.get_block_of_period(0), 0)
        self.assertEqual(empty.get_block_of_period(2), 2)
        self.assertEqual(empty.get_block_of_period(-2), -2)
        self.assertEqual(empty.get_label_of_periods([0]), "Stunde 0")
        self.assertEqual(empty.get_label_of_periods([0, 1, 2, 3]), "Stunden 0-3")

    def test_out_of_bounds(self):
        block_config = BlockConfiguration({1: [1, 2], 2: [3, 4]})

        self.assertEqual(block_config.get_periods_of_block(1), [1, 2])
        self.assertEqual(block_config.get_periods_of_block(2), [3, 4])

        self.assertEqual(block_config.get_periods_of_block(0), [0])
        self.assertEqual(block_config.get_periods_of_block(-1), [-1])
        self.assertEqual(block_config.get_periods_of_block(3), [5])
        self.assertEqual(block_config.get_periods_of_block(4), [6])

        self.assertEqual(block_config.get_block_of_period(1), 1)
        self.assertEqual(block_config.get_block_of_period(2), 1)
        self.assertEqual(block_config.get_block_of_period(3), 2)
        self.assertEqual(block_config.get_block_of_period(4), 2)

        self.assertEqual(block_config.get_block_of_period(-1), -1)
        self.assertEqual(block_config.get_block_of_period(0), 0)
        self.assertEqual(block_config.get_block_of_period(5), 3)
        self.assertEqual(block_config.get_block_of_period(6), 4)

        self.assertEqual(block_config.get_label_of_periods([1, 2]), "Block 1")
        self.assertEqual(block_config.get_label_of_periods([3, 4]), "Block 2")
        self.assertEqual(block_config.get_label_of_periods([1, 3]), "Stunden 1,3")
        self.assertEqual(block_config.get_label_of_periods([1, 2, 3, 4, 5]), "Stunden 1-5")
        self.assertEqual(block_config.get_label_of_periods([1, 2, 3, 4, 6]), "Stunden 1-4,6")
        self.assertEqual(block_config.get_label_of_periods([0]), "Stunde 0")


if __name__ == '__main__':
    unittest.main()
