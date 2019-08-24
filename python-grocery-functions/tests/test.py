from unittest import TestCase


class Basic(TestCase):
    def test_simple(self):
        self.assertEqual(True, not False)
