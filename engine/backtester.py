import pandas as pd
from one4all.backtesting import run_multiple_strategies
from one4all.strategy import DCA
from one4all.utils import ParameterGrid, spawn_strategy, transform_timeframe
from one4all.signals import bollinger_bands_series, RSI

#  1. Load and filter the data
# ----------------------------------------------------------------------------------------------------------------------
# Cargar datos de prueba
df = pd.read_csv('sample_data/ETHUSDT_010121_080921.csv',
                 parse_dates=['open_time', 'close_time'])

# Modificar los rangos de fecha
START_TIMEDATE = '2021-09-01 23:59:00'
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

boll = bollinger_bands_series(OHLC['Close'], MA_LENGTH=20)
print('Total posible de opciones para entrar: ' + str(len(SIGNAL)))

SIGNAL = [False for x in range(OHLC.shape[0])]
AUX = False
for i in range(len(boll)):
    BOLL = boll[i]
    CLOSE = OHLC.loc[boll.index[i]]['Close']
    if (AUX == False) and (CLOSE < BOLL):
        # Preparar terreno para evaluar re-ingreso
        AUX = True
    elif AUX and (CLOSE > BOLL):
        # Evaluar re-ingreso
        SIGNAL[OHLC.loc[:boll.index[i], :].shape[0]] = True
        #SIGNAL[i] = True
        AUX = False


print('Numero de senales para entrar ' + str(sum(SIGNAL)))


# 3.3 Create a signal using just RSI


# 3.4 Create a signal using bollinger bands and RSI


# 4. Run the backtester using multiple strategies
# ----------------------------------------------------------------------------------------------------------------------
eval = run_multiple_strategies(spawn_strategy(DCA, candidates), OHLC, signal=SIGNAL)
print(eval)

# 5. Store the results
# ----------------------------------------------------------------------------------------------------------------------
# eval.to_csv('./output_data/summary_report_30122022.csv', index_label='Parameters')
