import pandas as pd
from one4all.backtesting import run_multiple_strategies
from one4all.strategy import DCA
from one4all.utils import ParameterGrid, spawn_strategy

# Cargar datos de prueba
df = pd.read_csv('sample_data/ETHUSDT_010121_080921.csv',
                 parse_dates = ['open_time', 'close_time'])


# Modificar los rangos de fecha
START_TIMEDATE = '2021-01-01 00:00:00'
END_TIMEDATE = '2021-01-05 23:59:00'

OHLC = df[['open', 'high', 'low', 'close', 'volume']]
OHLC.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
OHLC.index = df['open_time']
OHLC = OHLC.loc[START_TIMEDATE:END_TIMEDATE]


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

# What is precisely a DCA objects? Can I use methods associated to this object?
eval = run_multiple_strategies(spawn_strategy(DCA, candidates), OHLC, signal=[True for x in range(OHLC.shape[0])])

print(eval)

# Store the results
eval.to_csv('./output_data/summary_report_30122022.csv')