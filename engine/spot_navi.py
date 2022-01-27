"""
navi.py
A bot using a custom signal with: BOLL15, BOLL30, and BOLL60 on ADAUSDT
"""
import time
import pandas as pd
from one4all.backtesting import run_multiple_strategies
from one4all.strategy import DCA
from one4all.utils import ParameterGrid, spawn_strategy
from one4all.signals import compute_boll_signal

#  1. Load and filter the data
# ----------------------------------------------------------------------------------------------------------------------
# Cargar datos de prueba
df = pd.read_csv('sample_data/ADAUSDT_010121_170122.csv',
                 parse_dates=['open_time', 'close_time'])

# Modificar los rangos de fecha
START_TIMEDATE = '2021-01-01 00:27:00'
END_TIMEDATE = '2022-01-08 21:59:00'

OHLC = df[['open', 'high', 'low', 'close', 'volume']]
OHLC.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
OHLC.index = df['open_time']

OHLC = OHLC.loc[START_TIMEDATE:END_TIMEDATE]
print('Numero de klines en OHLC: ' + str(OHLC.shape[0]))
#print(OHLC.head())
#print(OHLC.tail())



#  2. Define parameter combinations to create the strategy candidates
# ----------------------------------------------------------------------------------------------------------------------
# Comision futuros: 0.05%
# Comision spot: 0.1%
param_grid = {'TP': [0.9],
              'bo_size': [125],
              'so_qty': [3],
              'size_1st_so': [125],
              'so_vol_scale': [1.5],
              'so_step': [3],
              'so_step_scale': [1, 1.25],
              'long': [True],
              'EC': [0.1]}

candidates = [p for p in ParameterGrid(param_grid)]
print('\nCandidatos a backtester: ' + str(len(candidates)))
print('---------------------------')


# 3. Create the signal vector
# ----------------------------------------------------------------------------------------------------------------------
BB_SERIES = [compute_boll_signal(OHLC, TIMEFRAME_LENGTH=15),
             compute_boll_signal(OHLC, TIMEFRAME_LENGTH=30),
             compute_boll_signal(OHLC, TIMEFRAME_LENGTH=60)]

SIGNAL_DF = pd.concat(BB_SERIES, axis=1)

# Crear spike or
SIGNAL_DF['SPIKE'] = SIGNAL_DF.sum(axis=1)
SIGNAL_DF['SPIKE_OR'] = SIGNAL_DF['SPIKE'] != 0

print('\nSignal activadas por tipo:')
print('---------------------------')
print(SIGNAL_DF.sum(axis=0))

# Ver timeframes con SPIKE_OR activados
#print(SIGNAL_DF.loc[SIGNAL_DF.SPIKE_OR == True])

# Seleccionar columnas como signal
SIGNAL = SIGNAL_DF.SPIKE_OR.tolist()


# 4. Run the backtester using multiple strategies
# ----------------------------------------------------------------------------------------------------------------------
print('\nResumen backtester por candidato:')
print('---------------------------')
start = time.time()
eval = run_multiple_strategies(spawn_strategy(DCA, candidates), OHLC, signal=SIGNAL)
end = time.time()
print(end - start)
print(eval)


# 5. Save the reports with the results
# ----------------------------------------------------------------------------------------------------------------------
#eval.to_csv('./output_data/spot_navi/batch_B1011.csv', index_label='Parameters')