"""
signals.py

This file contains signal functions to enter into the market.
"""
from typing import List


from one4all.utils import transform_timeframe
import numpy as np
import pandas as pd
import ta as ta


def SMA(x, MA_LENGTH=14):
    """
    Compute and return a simple moving average
    :param x: a pandas series
    :param MA_LENGTH: the windows frame over which it's computed the mean
    :return: the moving average mean completing with NA at left
    """
    return x.rolling(window=MA_LENGTH, closed='right').mean()


def bollinger_bands_series(x, MA_LENGTH=20, SD_DEV=2.0):
    """
    Compute and return upper and lower bollinger band using as the typical price
    the close price.

    Usage:
      DF = bollinger_bands_series(OHLC['Close'], MA_LENGTH=20, TIMEFRAME_LENGTH_30)

    :param x: A pd.Series containing price informacion such as open, high, low and close prices
    :param MA_LENGTH: Number of prices used for computing the aggregate metrics
    :return: a pd.Series with the close price moving average, the lower and upper bollinger bands
    """
    # use as a typical price the close price
    tp = x
    tp_ma = tp.rolling(window=MA_LENGTH, closed='right').mean()

    # Notice that degree of freedom default parameter changes between np.std(ddof=0) and pd.DataFrame.std(ddof=1)
    tp_std = tp.rolling(window=MA_LENGTH, closed='right').std(ddof=0)
    bolu = tp_ma + SD_DEV * tp_std
    boll = tp_ma - SD_DEV * tp_std

    # eliminate NA (first observations)
    bolu = bolu[~bolu.isna()]
    boll = boll[~boll.isna()]
    tp_ma = tp_ma[~tp_ma.isna()]

    return pd.DataFrame({'price_SMA': tp_ma,
                         'BOLL': boll,
                         'BOLU': bolu})


def bollinger_bands_OHLC(OHLC, TIMEFRAME_LENGTH=60, MA_LENGTH=20, SD_DEV=2.0):
    """
    Compute and return upper and lower bollinger band using as the typical price
    the close price.
    Usage:
      DF = bollinger_bands_OHLC(OHLC, MA_LENGTH=20, TIMEFRAME_LENGTH_30)
      DF.columns = ['Close_SMA', 'BOLL', 'BOLU']

    :param OHLC: A pd.DataFrame containing kline information with open, high, low and close prices in each row
    :param TIMEFRAME_LENGTH: The timeframe length for each kline applied previous to compute bollinger band information
    :param MA_LENGTH: Number of klines used for computing the aggregate metrics
    :return: a pd.DataFrame with the close price moving average, the lower and upper bollinger bands
    """
    # transform OHLC to the specified timeframe length
    data = transform_timeframe(OHLC, TIMEFRAME_LENGTH)

    # use as a typical price the close price
    tp = data['Close']
    tp_ma = tp.rolling(window=MA_LENGTH, closed='right').mean()

    # Notice that degree of freedom default parameter changes between np.std(ddof=0) and pd.DataFrame.std(ddof=1)
    tp_std = tp.rolling(window=MA_LENGTH, closed='right').std(ddof=0)
    bolu = tp_ma + SD_DEV * tp_std
    boll = tp_ma - SD_DEV * tp_std

    # eliminate NA (first observations)
    bolu = bolu[~bolu.isna()]
    boll = boll[~boll.isna()]
    tp_ma = tp_ma[~tp_ma.isna()]

    return pd.DataFrame({'Close_SMA': tp_ma,
                         'BOLL': boll,
                         'BOLU': bolu})


def boll_signal(OHLC, boll, boll_index):
    """
    Compute the signal using bollinger lower band
    :param OHLC: kline information with open, high, low and close prices
    :param boll:
    :param boll_index:
    :return: a bool list with the signal for entry to the market
    """
    signal: List[bool] = [False for _ in range(OHLC.shape[0])]
    AUX = False
    for i in range(len(boll_index)):
        BOLL = boll[i]
        CLOSE = OHLC.iloc[boll_index[i]]['Close']
        if (AUX == False) and (CLOSE < BOLL):
            # preparar terreno para evaluar re-ingreso
            AUX = True
        elif AUX and (CLOSE > BOLL):
            # evaluar re-ingreso
            signal[boll_index[i]] = True
            AUX = False
    return signal

def RSI(OHLC, MA_LENGTH=14, RSI_LENGTH=14):
    """
    No da igual que tradingview, implementar manual la exponential moving average
    que utiliza Pine (ver al final de este archivo).
    Por ahora se esta utilizando ta.momentum.rsi() de la libreria
    de analisis tecnico:
    https://technical-analysis-library-in-python.readthedocs.io/en/latest/

    Ver ademas esta implementacion del rsi (tp da igual):
    https://github.com/lukaszbinden/rsi_tradingview/blob/main/rsi.py

    :param OHLC:
    :param MA_LENGTH:
    :param RSI_LENGTH:
    :return:
    """
    close_price = OHLC['Close']
    delta = close_price.diff()

    up, down = delta.copy(), delta.copy()
    ALPHA = 2 / (RSI_LENGTH + 1)
    #ALPHA = 1 / RSI_LENGTH

    up[up < 0] = 0
    up = pd.Series.ewm(up, alpha=ALPHA, adjust=False).mean()

    down[down > 0] = 0
    down *= -1
    down = pd.Series.ewm(down, alpha=ALPHA, adjust=False).mean()

    rsi = np.where(up == 0, 0, np.where(down == 0, 100, 100 - (100 / (1 + up / down))))

    ema = pd.Series.ewm(close_price, alpha=ALPHA, adjust=False).mean()
    return ta.momentum.rsi(close_price, window=RSI_LENGTH)

    #return pd.DataFrame({
    #                     'close_price': close_price,
    #                     'RSI2': ta.momentum.rsi(close_price, window=RSI_LENGTH),
    #                     'EMA': ema,
    #                     'EMA2': ta.trend.ema_indicator(close_price, window=MA_LENGTH)})


# on Pine ta.ema and ta.rma are exactly an exponential moving average the only distinction is that the former used
# alpha = 2 / (len + 1). On the other hand, the later used as alpha = 1 / len.
# Implementing the below code for computing the exponential moving average should solve the problem
#//the same on pine
#pine_ema(src, length) =>
#    alpha = 2 / (length + 1)
#    sum = 0.0
#    sum := na(sum[1]) ? ta.sma(src, length) : alpha * src + (1 - alpha) * nz(sum[1])
#plot(pine_ema(close,15))


#plot(ta.rma(close, 15))
#//the same on pine
#pine_rma(src, length) =>
#	alpha = 1/length
#	sum = 0.0
#	sum := na(sum[1]) ? ta.sma(src, length) : alpha * src + (1 - alpha) * nz(sum[1])
#plot(pine_rma(close, 15))