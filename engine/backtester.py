import numpy as np
import pandas as pd
from one4all.backtesting import run_multiple_strategies
from one4all.strategy import DCA
from one4all.utils import ParameterGrid, spawn_strategy, transform_timeframe
from one4all.signals import bollinger_bands_series, compute_boll_signal, project_signal_to, RSI, bollinger_bands_OHLC, compute_rsi_signal

#  1. Load and filter the data
# ----------------------------------------------------------------------------------------------------------------------
# Cargar datos de prueba
df = pd.read_csv('sample_data/ETHUSDT_011121_150122.csv',
                 parse_dates=['open_time', 'close_time'])

# Modificar los rangos de fecha
START_TIMEDATE = '2022-01-01 00:00:00'
END_TIMEDATE = '2022-01-08 23:59:00'

OHLC = df[['open', 'high', 'low', 'close', 'volume']]
OHLC.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
OHLC.index = df['open_time']

OHLC = OHLC.loc[START_TIMEDATE:END_TIMEDATE]
print('Number of klines in OHLC: ' + str(OHLC.shape[0]))
#print(OHLC.tail())


#  2. Define parameter combinations to create the strategy candidates
# ----------------------------------------------------------------------------------------------------------------------
param_grid = {'TP': [.5, ],
              'bo_size': [500],
              'so_qty': [8, 4],
              'size_1st_so': [500],
              'so_vol_scale': [1.1],
              'so_step': [2.5],
              'so_step_scale': [1.3],
              'long': [True],
              'EC': [.0005]}

candidates = [p for p in ParameterGrid(param_grid)]

# 3. Create the signal vector
# ----------------------------------------------------------------------------------------------------------------------
# 3.1 For ASAPers bots the signal is a constant vector with just True values
#SIGNAL = [True for x in range(OHLC.shape[0])]

# 3.2 Create a signal using bollinger bands

# 3.2.1 Create a signal using just one bollinger band use one of the below function
#BB10_SIGNAL = compute_boll_signal(OHLC, TIMEFRAME_LENGTH=10)
#BB15_SIGNAL = compute_boll_signal(OHLC, TIMEFRAME_LENGTH=15)
#BB30_SIGNAL = compute_boll_signal(OHLC, TIMEFRAME_LENGTH=30)
#BB60_SIGNAL = compute_boll_signal(OHLC, TIMEFRAME_LENGTH=60)

# 3.2.2 Create a signal using multiple bollinger band signals with different timeframe length
BB_SERIES = [compute_boll_signal(OHLC, TIMEFRAME_LENGTH=10),
             compute_boll_signal(OHLC, TIMEFRAME_LENGTH=15),
             compute_boll_signal(OHLC, TIMEFRAME_LENGTH=30),
             compute_boll_signal(OHLC, TIMEFRAME_LENGTH=60),
             compute_boll_signal(OHLC, TIMEFRAME_LENGTH=240)]

# 3.2.3 Contatenate all bollinger band series into a single dataframe
SIGNAL_DF = pd.concat(BB_SERIES, axis=1)
#print(SIGNAL_DF.sum(axis=0))

# 3.2.4 Project the signal with higer timeframe to compare with the lower ones
#SIGNAL_DF['PROJ_BB240'] = project_signal_to(SIGNAL_DF['BB240'], n_min=240)
#SIGNAL_DF['PROJ_BB60'] = project_signal_to(SIGNAL_DF['BB60'], n_min=60)
#SIGNAL_DF['PROJ_BB30'] = project_signal_to(SIGNAL_DF['BB30'], n_min=30)
#SIGNAL_DF['PROJ_BB30'] = project_signal_to(SIGNAL_DF['BB30'], n_min=15)

# 3.2.5 Compute the column 'SPIKE_AND' that look for BB in different timeframes coincide to activate
#PROJECTED_COLS = [col for col in SIGNAL_DF if col.startswith('PROJ')]
#SIGNAL_DF['SPIKE_AND30_60'] = SIGNAL_DF['BB30'] * SIGNAL_DF['PROJ_BB60']
#SIGNAL_DF['SPIKE_AND15_30'] = SIGNAL_DF['BB15'] * SIGNAL_DF['PROJ_BB30']
#SIGNAL_DF['SPIKE_AND15_60'] = SIGNAL_DF['BB15'] * SIGNAL_DF['PROJ_BB60']
#SIGNAL_DF['SPIKE_AND10_60'] = SIGNAL_DF['BB10'] * SIGNAL_DF['PROJ_BB60']
#SIGNAL_DF['SPIKE_AND10_240'] = SIGNAL_DF['BB10'] * SIGNAL_DF['PROJ_BB240']

#print(SIGNAL_DF.loc[SIGNAL_DF['SPIKE_AND10_240'] == True])
#print(SIGNAL_DF.loc[SIGNAL_DF['BB60'] == True], 'BB60')

#BB15_OHLC=bollinger_bands_OHLC(OHLC, TIMEFRAME_LENGTH=15).loc['2022-01-04 15:00:00':'2022-01-04 17:30:00']
#TF15=compute_boll_signal(OHLC, TIMEFRAME_LENGTH=15).loc['2022-01-03 15:00:00':'2022-01-03 17:30:00']
#TF30=compute_boll_signal(OHLC, TIMEFRAME_LENGTH=30).loc['2022-01-03 16:00:00':'2022-01-03 17:30:00']
#print(compute_boll_signal(OHLC, TIMEFRAME_LENGTH=15))


# 3.2.6 Compute the column 'SPIKE_OR' that look for BB signasl with different timeframes
#print(SIGNAL_DF)
#SIGNAL_DF['SPIKE'] = SIGNAL_DF.sum(axis=1)
#SIGNAL_DF['SPIKE_OR'] = SIGNAL_DF['SPIKE'] > 1


# Note: You want to run a backtester using one of the above signals?
# Choose SPIKE_OR/SPIKE_AND OR whatever column you want as a SIGNAL vector for the backtester...
#SIGNAL = SIGNAL_DF['SPIKE_OR'].to_list()


# 3.3 Create a RSI signal using the signal function compute_rsi_signal from signal.py
RSI30_70 = compute_rsi_signal(OHLC, TIMEFRAME_LENGTH=30, RSI_OBJ=70)


# 3.4 Create a signal using bollinger bands and RSI: add the above rsi as columns in SIGNAL_DF
SIGNAL_DF['RSI30_70']=RSI30_70

# 3.4.1 Combine signals using AND or OR

# 4. Run the backtester using multiple strategies
# ----------------------------------------------------------------------------------------------------------------------
#eval = run_multiple_strategies(spawn_strategy(DCA, candidates), OHLC, signal=SIGNAL)
#print(eval)


# 5. Save the reports with the results
# ----------------------------------------------------------------------------------------------------------------------
# eval.to_csv('./output_data/summary_report_30122022.csv', index_label='Parameters')