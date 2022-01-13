"""
utils.py

This file contains utility functions.
"""
from collections.abc import Mapping, Iterable
from functools import partial, reduce
from itertools import product
import pandas as pd
import operator

def transform_timeframe(OHLC, TIMEFRAME_LENGTH):
    """
    Given a OHLC dataframe with 1 minutes klines, transform_timeframe returns a transformation with aggregate
    klines (like 15, 30 or 60 minutes).

    TODO: Crear un assertions cuando no calzen el TIMEFRAME_LENGTH con el numero de klines en el OHLC o algo que
    arroje un error explicito (HACER UN TEST CASE PARA ESTO)

    :param OHLC: a pandas dataframe with open, high, low, and close prices. As well, a open_time index
    :param TIMEFRAME_LENGTH: a float specified the new timeframe conversion required
    :return: OHLC converted into the timeframe specified
    """
    open_price = OHLC['Open'].iloc[[x for x in range(0, OHLC.shape[0], TIMEFRAME_LENGTH)]]
    close_price = OHLC['Close'].iloc[[x + (TIMEFRAME_LENGTH-1) for x in range(0, OHLC.shape[0], TIMEFRAME_LENGTH)]]
    high_price = [OHLC.iloc[int(x):int(x + (TIMEFRAME_LENGTH - 1)), OHLC.columns.get_loc('High')].max() for x in range(0, OHLC.shape[0], TIMEFRAME_LENGTH)]
    low_price = [OHLC.iloc[int(x):int(x + (TIMEFRAME_LENGTH - 1)), OHLC.columns.get_loc('Low')].min() for x in range(0, OHLC.shape[0], TIMEFRAME_LENGTH)]
    close_price.index = open_price.index
    return pd.DataFrame({'Open': open_price,
                         'High': high_price,
                         'Low': low_price,
                         'Close': close_price})


def spawn_strategy(cls, parameter_grid):
    """
    Given a collection of parameters set; create a dictionary with the given cls instantiated
    with every set. Create an ID as key given 'A' + id number from A0, A1, ..., A999
    :param cls: give a strategy classes (e.g. DCA) with a default set of parameters
    :param parameter_grid:
    :return: A dict with instantiation cls given the ParameterGrid
  """
    spawn = [cls(**param) for param in parameter_grid]
    return {'A' + str(i): x for i, x in enumerate(spawn)}


class ParameterGrid:
    """
    Minimal functionality based on Scikit-learn h class
    - dic: parameter name as key and as value a list of candidate value
    """

    def __init__(self, param_grid):
        if isinstance(param_grid, Mapping):
            # support either dict or list of dicts
            param_grid = [param_grid]

        # check if all entries are dictionaries of lists
        for grid in param_grid:
            if not isinstance(grid, dict):
                raise TypeError('Parameter grid is not a dict ({!r})'.format(grid))

        for key in grid:
            if not isinstance(grid[key], Iterable):
                raise TypeError('Parameter grid is not a dict ({!r})'.format(grid))

        self.param_grid = param_grid

    def __iter__(self):
        """
        Iterate over the points in the grid.
        Returns
        -------
        params : iterator over dict of str to any
        Yields dictionaries mapping each estimator parameter to one of its
        allowed values.
        """
        for p in self.param_grid:
            # Always sort the keys of a dictionary, for reproducibility
            items = sorted(p.items())
            if not items:
                yield {}
            else:
                keys, values = zip(*items)
                for v in product(*values):
                    params = dict(zip(keys, v))
                    yield params

    def __len__(self):
        product = partial(reduce, operator.mul)
        return sum(product(len(v) for v in p.values()) if p else 1
                   for p in self.param_grid)
