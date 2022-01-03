"""
strategy.py

This file contains the classes that implement strategies for backtesting.
"""
from .backtesting import *


class Strategy(object):
    # Allow us to initialize a custom strategy from a parameter dict
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.strategy_pos = []
        self.so_magazine = []

    @property
    def get_params(self):
        return {k: getattr(self, k) for k in self.__slots__}

    @property
    def __repr__(self):
        return '<Strategy: ' + str(self.get_params()) + '>'


class DCA(Strategy):
    __slots__ = ['TP', 'bo_size', 'long', 'size_1st_so', 'so_qty', 'so_step', 'so_step_scale', 'so_vol_scale', 'EC']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    #@property
    def compute_min_capital(self):
        aux = 1
        if not self.long:
            aux = -1
        order_size = [self.bo_size] + [self.size_1st_so * aux * self.so_vol_scale ** x for x in range(self.so_qty)]
        return sum(order_size)

    def track_drawdown(self, last_OLHC):
        if (len(self.strategy_pos)) != 0:
            if self.long:
                self.strategy_pos[-1].lowest_low(last_OLHC)
            else:
                self.strategy_pos[-1].highest_high(last_OLHC)

    def track_best_try(self, last_OLHC):
        if (len(self.strategy_pos)) != 0:
            if self.long:
                self.strategy_pos[-1].try_high(last_OLHC)
            else:
                self.strategy_pos[-1].try_low(last_OLHC)

    def open_position(self, OLHC):
        self.strategy_pos.append(Position(self.TP))
        self.strategy_pos[-1].new_entry(self.bo_size, OLHC['Open'][-1], OLHC.index[-1], self.TP)

    def clean_so_magazine(self):
        """
        Update so_magazine attribute keeping just the orders were not filled
        """
        self.so_magazine = [o for o in self.so_magazine if o.filled == False]

    def eval_so(self, OLHC):
        if self.long:
            for o in self.so_magazine:
                o.filled = OLHC['Low'][-1] < o.price
                if o.filled:
                    self.track_best_try(OLHC.iloc[-1])
                    self.strategy_pos[-1].new_entry(o.size, o.price, OLHC.index[-1], self.TP)
            self.clean_so_magazine()
        else:
            for o in self.so_magazine:
                o.filled = OLHC['High'][-1] > o.price
                if o.filled:
                    self.track_best_try(OLHC.iloc[-1])
                    self.strategy_pos[-1].new_entry(o.size, o.price, OLHC.index[-1], self.TP)
            self.clean_so_magazine()

    def next(self, OLHC, signal):
        if len(self.strategy_pos) != 0:
            if not self.strategy_pos[-1].is_closed():
                # evaluar si se puede cerrar la posicion (self.EC incorpora la comision del exchange)
                if OLHC['High'][-1] > (self.strategy_pos[-1].weighted_price * (1 + (self.TP + self.EC) / 100)):
                    self.track_best_try(OLHC.iloc[-1])
                    self.strategy_pos[-1].close_entry(self.strategy_pos[-1].weighted_price * (1 + (self.TP + self.EC) / 100), OLHC.index[-1])
                else:
                    # evaluar si una safe order se gatilla:
                    self.eval_so(OLHC)

            else:
                # Agregar senal para el caso ASAP, la senal es simpre True
                if signal:
                    self.open_position(OLHC)
                    self.so_magazine = create_safe_order(self.so_qty, OLHC['Open'][-1], OLHC.index[-1], self.size_1st_so,
                                                         self.so_vol_scale, self.so_step, self.so_step_scale, self.long)
                    # evaluar safeorder
                    self.eval_so(OLHC)

        else:
            # agregar senal: para el caso ASAP, la senal siempre es True
            if signal:
                self.open_position(OLHC)
                self.so_magazine = create_safe_order(self.so_qty, OLHC['Open'][-1], OLHC.index[-1], self.size_1st_so,
                                                     self.so_vol_scale, self.so_step, self.so_step_scale, self.long)
                # evaluar safeorder
                self.eval_so(OLHC)
        # track drawdown
        self.track_drawdown(OLHC.iloc[-1])
        self.track_best_try(OLHC.iloc[-1])



