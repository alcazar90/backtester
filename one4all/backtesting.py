"""
backtesting.py

This file contains the classes that create the backtesting engine.

NOTA:!!

Se desactivo el registro del best_try para correr mas rapido las estrategias, leer lo siiguiente con atencion.

Para desactivar seguir el best_try (ojala por eficiencia), comentar las siguientes lineas de codigo:
 - strategy.py, linea 69, 76, 85 y 110
 - backtesting.py, lineas 69-73

"""
from collections.abc import Mapping, Sequence, Iterable
from datetime import datetime
from itertools import accumulate, product
from functools import partial, reduce
import operator
import numpy as np
import pandas as pd
import random as random
from .reports import *


class Order:
    def __init__(self, size, price, date):
        self.size = size
        self.price = price
        self.date = date
        self.filled = False
        self.best_try = {'price': 0,
                         'price_index': 0,
                         'date': self.date,
                         'pct': 0}

    @property
    def is_long(self):
        return self.size > 0

    @property
    def is_short(self):
        return self.size < 0


def create_safe_order(so_qty, price, date, size_1st_so=12, so_vol_scale=2, so_step=0.37, so_step_scale=1.3, long=True):
    aux = 1
    if long == False: aux = 1
    order_size = [size_1st_so * aux * so_vol_scale ** x for x in range(so_qty)]
    mult_factor = list(accumulate([1 + (so_step * -aux / 100 * so_step_scale ** x) for x in range(so_qty)],
                                  lambda x, y: x * y))
    trigger_price = [round(price * factor, 7) for factor in mult_factor]
    so_info = list(zip(order_size, trigger_price))
    return [Order(so[0], so[1], date) for so in so_info]


class Position:
    def __init__(self, TP):
        self.pos = 0
        self.weighted_price = 0
        self.order_list = []
        self.closed = False
        self.TP = TP
        self.TP_price = 0
        self.drawdown = {'price': 0,
                         'date': None,
                         'pct': 0,
                         'pct_float': 0}

    def new_entry(self, size, price, date, TP):
        """Gives size and price"""
        # assert self.closed == False, 'Position closed'
        self.order_list.append(Order(size, price, date))
        self.weighted_price = (self.pos * self.weighted_price + size * price) / (self.pos + size)
        self.TP_price = round(self.weighted_price * (1 + TP / 100), 7)
        self.pos += size
        if len(self.order_list) == 1:
            self.drawdown['price'] = self.weighted_price
        # if len(self.order_list) == 1:
        #    self.order_list[-1].best_try['price'] = self.weighted_price
        #    self.order_list[-1].best_try['price_index'] = \
        #        round((self.order_list[-1].best_try['price'] - self.order_list[-1].price) / (
        #                self.TP_price - self.order_list[-1].price), 7)

    def close_entry(self, price, date):
        """Close all position creating a new order"""
        self.order_list.append(Order(-self.pos, price, date))
        self.closed = True

    def get_pl(self, close_price):
        """
        :param: close_price
        :return: print the profit and loss
        """
        pl = 0
        if self.pos < 0:
            pl = round(self.pos + (self.weighted_price - close_price) / abs(self.pos * self.weighted_price), 4)
        else:
            pl = round(self.pos + (self.weighted_price - close_price) / abs(self.pos * self.weighted_price), 4)
        return print(f'{pl * 100}%')

    def get_pos(self):
        return self.pos

    def get_weighted_price(self):
        return self.weighted_price

    def is_long(self):
        return self.pos > 0

    def is_short(self):
        return self.pos < 0

    def is_closed(self):
        return self.closed

    def try_high(self, last_OLHC):
        """
        Record best try for long strategies
        :param last_OLHC:
        :return: None
        """
        if self.order_list[-1].best_try['price'] < last_OLHC['High']:
            # compute min between 'High' and self.TP_price
            update_price = min(last_OLHC['High'], self.TP_price)
            # update best_price
            self.order_list[-1].best_try['price'] = update_price
            # compute price index using last entry price and TP_price
            self.order_list[-1].best_try['price_index'] = \
                round((update_price - self.order_list[-1].price) / (self.TP_price - self.order_list[-1].price), 7)
            # record the date
            self.order_list[-1].best_try['date'] = last_OLHC.name  # pd.df index -> pd.series is name

    def try_low(self, last_OLHC):
        # record best try for short strategies
        if self.order_list[-1].best_try['price'] > last_OLHC['Low']:
            self.order_list[-1].best_try['price'] = max(last_OLHC['Low'], self.TP_price)
            self.order_list[-1].best_try['date'] = last_OLHC.name  # pd.df index -> pd.series name

    def lowest_low(self, last_OLHC):
        # drawdown for long strategies
        if self.drawdown['price'] > last_OLHC['Low']:
            self.drawdown['price'] = last_OLHC['Low']
            self.drawdown['date'] = last_OLHC.name  # pd.df index -> pd.series name
            self.drawdown['pct'] = ''.join(
                [str(round((self.drawdown['price'] / self.order_list[0].price - 1) * 100, 2)), '%'])
            self.drawdown['pct_float'] = self.drawdown['price'] / self.order_list[0].price - 1

    def highest_high(self, last_OLHC):
        # drawdown for short strategies
        if self.drawdown['price'] < last_OLHC['High']:
            self.drawdown['price'] = last_OLHC['High']
            self.drawdown['date'] = last_OLHC.name  # pd.df index -> pd.series name
            self.drawdown['pct'] = ''.join(
                [str(round((self.drawdown['price'] / self.order_list[0].price - 1) * 100, 2)), '%'])
            self.drawdown['pct_float'] = self.drawdown['price'] / self.order_list[0].price - 1


def backtesting(strategy, OHLC, signal, DRAWDOWN_TOLERANCE):
    """
    :param strategy:
    :param OHLC: a dataframe with open, high, low, close price information
    :param signal: a boolean list with the same length that OHLC's number of rows
    :return: a list with close deals given a strategy run in time range indicated by OHLC
    """
    NROW = OHLC.shape[0]
    for i in range(NROW):
        # agregar linea con tolerancia de max drawdown para parar estrategia de manera temprana
        strategy.next(OHLC.iloc[0:(i + 1), :], signal[i])
        if len(strategy.strategy_pos) != 0:
            if strategy.strategy_pos[-1].drawdown['pct_float'] < DRAWDOWN_TOLERANCE:
                print('early stop')
                print(strategy.strategy_pos[-1].drawdown)
                break
    return strategy.strategy_pos


def eval_strategies(strategy_dic, OHLC, signal, DRAWDOWN_TOLERANCE):
    """
    Run backtesting over different strategies and collect the report.
    :param strategy_dic:
    :param OHLC:
    :param signal:
    :return: a dictionary with a report_list by each strategy instance
    """
    output = {key: [] for key in strategy_dic.keys()}
    N = 1
    for s in strategy_dic.keys():
        back_result = backtesting(strategy_dic[s], OHLC, signal, DRAWDOWN_TOLERANCE)
        output[s] += back_result
        if N % 2 == 0: print('Progress:', round(N / len(strategy_dic), 4) * 100)
        N += 1
    return output


def run_multiple_strategies(strategy_dic, OHLC, signal, DRAWDOWN_TOLERANCE=-0.35):
    C = random.choice(list(strategy_dic.values()))
    info_by_strategy = eval_strategies(strategy_dic, OHLC, signal, DRAWDOWN_TOLERANCE)
    # results = []
    results = [summary_strategy(make_report(deals), MIN_CAPITAL=strategy_dic[name].compute_min_capital()) for
               name, deals in info_by_strategy.items()]
    # for name, deals in info_by_strategy.items():
    #    results.append(summary_strategy(make_report(deals), MIN_CAPITAL=strategy_dic[name].compute_min_capital))
    results = pd.concat(results, axis=1)
    results.columns = [name for name in info_by_strategy.keys()]
    strategy_settings = [pd.DataFrame.from_dict(strategy_dic[k].get_params, orient='index') for k in strategy_dic]
    strategy_settings = pd.concat(strategy_settings, axis=1)
    strategy_settings.columns = [name for name in info_by_strategy.keys()]
    results = pd.concat([results, strategy_settings], axis=0)
    return results
