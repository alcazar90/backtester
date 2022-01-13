import pandas as pd
from one4all.backtesting import run_multiple_strategies
from one4all.strategy import DCA
from one4all.utils import ParameterGrid, spawn_strategy, transform_timeframe
from one4all.signals import bollinger_bands_series, compute_boll_signal, RSI

#  1. Load and filter the data
# ----------------------------------------------------------------------------------------------------------------------
# Cargar datos de prueba
df = pd.read_csv('sample_data/ETHUSDT_010121_080921.csv',
                 parse_dates=['open_time', 'close_time'])

# Modificar los rangos de fecha
START_TIMEDATE = '2021-09-01 23:00:00'
END_TIMEDATE = '2021-09-07 23:59:00'

OHLC = df[['open', 'high', 'low', 'close', 'volume']]
OHLC.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
OHLC.index = df['open_time']
# OHLC = OHLC.loc[START_TIMEDATE:END_TIMEDATE]
# SUBSET HOURLY KLINES
OHLC = OHLC.loc[START_TIMEDATE:END_TIMEDATE]
# print(OHLC)


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
SIGNAL = [True for x in range(OHLC.shape[0])]

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
             compute_boll_signal(OHLC, TIMEFRAME_LENGTH=60)]

# concatena all bollinger band series into one dataframe
SIGNAL_DF = pd.concat(BB_SERIES, axis=1)

# Create the 'SPIKE' column which sum how many signal are activated by row
# Then, compute 'SPIKE_OR' and indicator column that signal whenever a bollinger signal is True in a timeframe
# In addition, compute 'SPIKE_AND' and indicator column that tells us when all bollinger signal are True in a timeframe
SIGNAL_DF['SPIKE'] = SIGNAL_DF.sum(axis=1)
SIGNAL_DF['SPIKE_OR'] = SIGNAL_DF['SPIKE'] != 0
SIGNAL_DF['SPIKE_AND'] = SIGNAL_DF['SPIKE'] == 4
print(SIGNAL_DF)

# Now, make a summary with stats about 'SPIKE_OR' and 'SPIKE_AND' and the whole bollinger dataframe
print(SIGNAL_DF.sum(axis=0))

# You want to run a backterster using one of the above signals?
SIGNAL = SIGNAL_DF['SPIKE_OR'].to_list()

# Choose SPIKE_OR/SPIKE_AND OR whatever column you want as a SIGNAL vector for the backtester...


# 3.3 Create a signal using just RSI
# TODO...


# 3.4 Create a signal using bollinger bands and RSI
# TODO...



# 4. Run the backtester using multiple strategies
# ----------------------------------------------------------------------------------------------------------------------
eval = run_multiple_strategies(spawn_strategy(DCA, candidates), OHLC, signal=SIGNAL)
print(eval)


# 5. Save the reports with the results
# ----------------------------------------------------------------------------------------------------------------------
# eval.to_csv('./output_data/summary_report_30122022.csv', index_label='Parameters')