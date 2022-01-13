"""
test.py

This file tests the various necessary util functions.
"""
from .utils import *
from .signals import *
import unittest
import pandas as pd
from pandas._testing import assert_series_equal, assert_frame_equal


class UTILSTest(unittest.TestCase):
    def setUp(self):
        """Read and OHLC dataset for test timeframe transformations from 1min to 15, 30 and 60 minutes klines"""
        self.OHLC = pd.read_csv('./engine/sample_data/ETHUSDT_010121_080921.csv',
                                parse_dates=['open_time', 'close_time'])
        self.START_TIMEDATE = '2021-09-01 00:00:00'
        self.END_TIMEDATE = '2021-09-01 23:59:00'
        self.OHLC.index = self.OHLC['open_time']
        self.OHLC = self.OHLC[self.START_TIMEDATE:self.END_TIMEDATE]
        self.OHLC = self.OHLC[['open', 'high', 'low', 'close']]
        self.OHLC.columns = ['Open', 'High', 'Low', 'Close']

    def test_parameterGrid(self):
        self.param_grid = {
            'TP': [.5],
            'bo_size': [100],
            'so_qty': [1, 2]
        }
        self.candidates = [p for p in ParameterGrid(self.param_grid)]
        self.assertEqual(len(self.candidates), 2)  # ParameterGrid don't generate the correct candidate's number

    def test_transform_timeframe15(self):
        """Compare two OHLC dataframes one downloading directly with 15min klines. The other one, a transform
        OHLC with 1 min klines into 15min using transform_timeframe function"""
        self.OHLC15min = pd.read_csv('./engine/sample_data/timeframe_test_210901_15min.csv',
                                     parse_dates=['open_time'], index_col=0)
        self.OHLC15min.columns = ['Open', 'High', 'Low', 'Close']
        #print(self.OHLC15min)
        #print(transform_timeframe(self.OHLC, 15).head())
        assert_frame_equal(self.OHLC15min, transform_timeframe(self.OHLC, 15).head())

    def test_transform_timeframe30(self):
        """Compare two OHLC dataframes one downloading directly with 30min klines. The other one, a transform
        OHLC with 1 min klines into 30min using transform_timeframe function"""
        self.OHLC30min = pd.read_csv('./engine/sample_data/timeframe_test_210901_30min.csv',
                                     parse_dates=['open_time'], index_col=0)
        self.OHLC30min.columns = ['Open', 'High', 'Low', 'Close']
        #print(self.OHLC30min)
        #print(transform_timeframe(self.OHLC, 30).head())
        assert_frame_equal(self.OHLC30min, transform_timeframe(self.OHLC, 30).head())

    def test_transform_timeframe60(self):
        """Compare two OHLC dataframes one downloading directly with 60min klines. The other one, a transform
        OHLC with 1 min klines into 60min using transform_timeframe function"""
        self.OHLC60min = pd.read_csv('./engine/sample_data/timeframe_test_210901_60min.csv',
                                     parse_dates=['open_time'], index_col=0)
        self.OHLC60min.columns = ['Open', 'High', 'Low', 'Close']
        #print(self.OHLC60min)
        #print(transform_timeframe(self.OHLC, 60).head())
        assert_frame_equal(self.OHLC60min, transform_timeframe(self.OHLC, 60).head())

class REPORTSTest(unittest.TestCase):
    def setup(self):
       """Create a custom Position object to generate a report from the data stored in them.
          It's necessary to import Order and Position classes to recreate the object...
       """
       # self.toy_report_df = pd.DataFrame({})
       pass

    def test_reports(self):
       pass


class SIGNALTest(unittest.TestCase):
    def setup(self):
        pass

    def test_SMA(self):
        self.x = pd.Series([2, 3, 1, 6, 2, 8])
        assert_series_equal(SMA(self.x, MA_LENGTH=2), pd.Series([np.nan, 2.5, 2.0, 3.5, 4.0, 5.0]))
        assert_series_equal(SMA(self.x, MA_LENGTH=3), pd.Series([np.nan,  np.nan, self.x[:3].sum()/3, self.x[1:4].sum()/3,
                                                              self.x[2:5].sum()/3,  self.x[3:6].sum()/3]))

        assert_series_equal(SMA(self.x, MA_LENGTH=4), pd.Series([np.nan,  np.nan, np.nan, self.x[:4].sum()/4,
                                                              self.x[1:5].sum()/4, self.x[2:6].sum()/4]))

    def test_bollSignal(self):
        """
        Create a custom pandas dataframe with close prices for evaluate boll signal using the lower band
        """
        self.boll_df = pd.DataFrame({'Close':[4, 8, 10, 11, 9, 18, 17, 16, 19]})
        self.assertEqual(boll_signal(self.boll_df, [9, 10, 19, 15], [1, 3, 5, 7]),
                         [False, False, False, True, False, False, False, True, False])

if __name__ == '__main__':
    unittest.main()
