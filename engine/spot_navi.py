"""
navi.py
A bot using a custom signal with: BOLL15, BOLL30, and BOLL60 on ADAUSDT
"""
import numpy as np
import pandas as pd
from one4all.backtesting import run_multiple_strategies, create_safe_order
from one4all.strategy import DCA
from one4all.utils import ParameterGrid, spawn_strategy, transform_timeframe
from one4all.signals import bollinger_bands_series, compute_boll_signal, project_signal_to, RSI, bollinger_bands_OHLC, compute_rsi_signal

#  1. Load and filter the data
# ----------------------------------------------------------------------------------------------------------------------
# Cargar datos de prueba
df = pd.read_csv('sample_data/ADAUSDT_011121_150122.csv',
                 parse_dates=['open_time', 'close_time'])

# Modificar los rangos de fecha
START_TIMEDATE = '2021-11-01 00:00:00'
END_TIMEDATE = '2022-01-08 23:59:00'

OHLC = df[['open', 'high', 'low', 'close', 'volume']]
OHLC.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
OHLC.index = df['open_time']

OHLC = OHLC.loc[START_TIMEDATE:END_TIMEDATE]
print('Numero de klines en OHLC: ' + str(OHLC.shape[0]))



#  2. Define parameter combinations to create the strategy candidates
# ----------------------------------------------------------------------------------------------------------------------
# Comision futuros: 0.05%
# Comision spot: 0.1%
param_grid = {'TP': [.5, .7],
              'bo_size': [125],
              'so_qty': [4],
              'size_1st_so': [125],
              'so_vol_scale': [2.0],
              'so_step': [2.0, 2.5, 3.0, 3.5],
              'so_step_scale': [1.3],
              'long': [True],
              'EC': [0.1]}

candidates = [p for p in ParameterGrid(param_grid)]
print('\nCandidatos a backtester: ')
print('---------------------------')
print(candidates)

#L = create_safe_order(4, 100, '2021-01-02', size_1st_so=125, so_vol_scale=2.0, so_step_scale=1.3, so_step=2.5)
#print([x.size for x in L])


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
eval = run_multiple_strategies(spawn_strategy(DCA, candidates), OHLC, signal=SIGNAL)
print(eval)


# 5. Save the reports with the results
# ----------------------------------------------------------------------------------------------------------------------
eval.to_csv('./output_data/summary_report_navy_18012022.csv', index_label='Parameters')