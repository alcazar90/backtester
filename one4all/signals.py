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
    return pd.Series(boll)

    #return pd.DataFrame({'price_SMA': tp_ma,
    #                     'BOLL': boll,
    #                     'BOLU': bolu})


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
                         'Close': data['Close'],
                         'BOLL': boll,
                         'BOLU': bolu})

def compute_boll_signal(OHLC, TIMEFRAME_LENGTH, MA=20, SD_DEV=2.0):
    """

    :param OHLC: kline information in minutes with open, high, low and close prices
    :param TIMEFRAME_LENGTH: the length for aggregate klines before computing the signal
    :return: a signal list with the same length that the number of rows of the given OHLC input
    """
    SIGNAL = [False for x in range(OHLC.shape[0])]
    AUX = False
    TRANS = TIMEFRAME_LENGTH
    OHLC_TRANS = transform_timeframe(OHLC, TIMEFRAME_LENGTH=TRANS)
    boll = bollinger_bands_series(OHLC_TRANS['Close'], MA_LENGTH=MA, SD_DEV=SD_DEV)
    for i in range(len(boll)):
        BOLL = boll[i]
        CLOSE = OHLC_TRANS.loc[boll.index[i]]['Close']
        if (AUX == False) and (CLOSE < BOLL):
            # Preparar terreno para evaluar re-ingreso
            AUX = True
        elif AUX and (CLOSE > BOLL):
            # Evaluar re-ingreso
            SIGNAL[OHLC.loc[:boll.index[i], :].shape[0] + (TRANS - 1)] = True
            AUX = False
    SIGNAL_DF = pd.DataFrame({'BB' + str(TRANS): SIGNAL})
    SIGNAL_DF.index = OHLC.index
    return SIGNAL_DF
    #return pd.dataframe({'close': ohlc['close'],
    #                     'close_30m': ohlc_trans['close'],
    #                     'boll30': boll,
    #                     'signal': signal})


def project_signal_to(signal, n_min):
    """
    Project True over the following n_min forward, usually the number of minute in which
    the BB_series was calculated

    :param signal: a bool pd.Series with a signal
    :param n_min: project signal to n_min forward
    :return: bool pd.Series with the same length but signal projected n_min
    """
    projected_signal = signal.copy()
    # get the indices in which the signal is true
    true_indices = np.where(projected_signal)[0]
    # project the signal during n_min forward
    for index in true_indices:
        projected_signal.iloc[index:(index + n_min)] = True
    return projected_signal


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


def compute_rsi_signal(OHLC, TIMEFRAME_LENGTH, RSI_LENGTH=14, RSI_OBJ=70, LOWER_THAN=True):
    """
    TODO: revisar el numero de NA que se utilizan en la ventana para computar el RSI;
    Deberian ser eliminados? Deberian quedar como NA? Ver las mismas consecuencias en el calculo de las bollinger
    cuando el numero de observaciones en menor a la ventana especificada.
    :param OHLC:
    :param TIMEFRAME_LENGTH:
    :param RSI_LENGTH:
    :param RSI_OBJ:
    :param LOWER_THAN:
    :return:
    """
    # Se utiliza el largo completo inicial del OHLC independiente de en cuanto se transforma el timestamp
    SIGNAL = [False for _ in range(OHLC.shape[0])]
    print(len(SIGNAL))
    TRANS = TIMEFRAME_LENGTH
    OHLC_TRANS = transform_timeframe(OHLC, TIMEFRAME_LENGTH=TRANS)
    rsi_series = RSI(OHLC_TRANS, RSI_LENGTH=RSI_LENGTH)
    AUX = False
    for i in range(len(rsi_series)):
        RSI_I = rsi_series[i]
        if AUX:
            SIGNAL[OHLC.loc[:rsi_series.index[i], :].shape[0]] = AUX
            AUX = False
        if LOWER_THAN:
            if RSI_I < RSI_OBJ:
                AUX = True
        else:
            if RSI_I > RSI_OBJ:
                AUX = True
    SIGNAL = pd.Series(SIGNAL)
    SIGNAL.index = OHLC.index
    return SIGNAL
