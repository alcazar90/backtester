"""
test.py

This file tests the various necessary util functions.
"""
from .utils import *
import unittest
import pandas as pd


class UTILSTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_parameterGrid(self):
        self.param_grid = {
            'TP': [.5],
            'bo_size': [100],
            'so_qty': [1, 2]
        }
        self.candidates = [p for p in ParameterGrid(self.param_grid)]
        print(self.candidates)
        self.assertEqual(len(self.candidates), 2)  # ParameterGrid don't generate the correct candidate's number


class REPORTSTest(unittest.TestCase):
    def setup(self):
       """Create a custom Position object to generate a report from the data stored in them.
          It's necessary to import Order and Position classes to recreate the object...
       """
       # self.toy_report_df = pd.DataFrame({})
       pass

    def test_reports(self):
       pass

if __name__ == '__main__':
    unittest.main()
