"""
reports.py

This file contains reporting functions.
"""
from typing import List, Union, Any
import pandas as pd
import numpy as np
from pandas import DataFrame
#from one4all.backtesting import Position


def make_report(strategy_pos, last_close_price = 800) -> DataFrame:
    """
    Extract the closed deals' information from strategy_position
    :type strategy_pos: Position
    :param strategy_pos: a list received from the backtester with position objects
    :param last_close_price:
    :return: a pd.DataFrame with summary metrics
    """
    close_deal = strategy_pos
    duration = [pos.order_list[-1].date - pos.order_list[0].date for pos in close_deal]

    # dummy variable indicating if the position is closed (open-close order)
    is_close = [1 if pos.is_closed() else 0 for pos in strategy_pos]
    # get open/close dates
    open_date = [pos.order_list[0].date for pos in close_deal]
    close_date = [pos.order_list[-1].date for pos in close_deal]
    # get open/close price
    open_price = [pos.order_list[0].price for pos in close_deal]
    close_price = [round(pos.order_list[-1].price, 2) for pos in close_deal]
    # get deal/order size
    deal_size = [abs(pos.order_list[-1].size) for pos in close_deal]
    order_size = [len(pos.order_list) for pos in close_deal]
    # get safeorder info for each deal: trigger prices and dates
    trigger_prices = [str([round(o.price, 2) for o in pos.order_list]) for pos in close_deal]
    trigger_dates = [str([o.date for o in pos.order_list]) for pos in close_deal]

    # compute p&l
    pnl_usd = [abs(pos.pos) * pos.weighted_price * pos.TP / 100 for pos in close_deal]
    #pnl_coinM: List[Union[float, Any]] = [abs(pos.pos) * pos.TP / 100 for pos in close_deal]
    pnl_coinM = [abs(pos.pos) * pos.TP / 100 for pos in close_deal]
    pnl_pct = [pos.TP for pos in close_deal]

    # extract drawdown info per deal
    date_drawdown = [pos.drawdown['date'] for pos in close_deal]
    price_drawdown = [pos.drawdown['price'] for pos in close_deal]
    pct_drawdown = [pos.drawdown['pct'] for pos in close_deal]

    # extract best_try info per deal
    price_best_try = [[o.best_try['price_index'] for o in pos.order_list] for pos in close_deal]
    date_best_try = [[o.best_try['date'] for o in pos.order_list] for pos in close_deal]

    # OJO: utiliza la instancia de strategy para obtener el ultimo precio utilizado
    # Se utiliza el argumento last_close_price
    current_usd = [coin * last_close_price for coin in pnl_coinM]

    report = pd.DataFrame({'open_date': open_date,
                           'close_date': close_date,
                           'is_close': is_close,
                           'duration': duration,
                           'order_size': order_size,
                           'open_price': open_price,
                           'close_price': close_price,
                           'deal_size': deal_size,
                           'pnl_usd': pnl_usd,
                           'pnl_coinM': pnl_coinM,
                           'pnl_pct': pnl_pct,
                           'coin_pnl_at_current_usd': current_usd,
                           'trigger_prices': trigger_prices,
                           'trigger_dates': trigger_dates,
                           'date_drawdown': date_drawdown,
                           'price_drawdown': price_drawdown,
                           'pct_drawdown': pct_drawdown,
                           'price_best_try': price_best_try,
                           'date_best_try': date_best_try
                           })
    report['num_safe_order'] = report.order_size - 2
    if np.any(report.is_close == 0):
        report.iloc[-1, -1] += 1
    return report


def summary_strategy(report, MIN_CAPITAL, LEVERAGE=1):
    """
    Summary the main information into a pd.Series given a report made by the function make_report
    :param report: a pd.DataFrame report
    :param MIN_CAPITAL:
    :param leverage:
    :return:
    """
    # MIN_CAPITAL se puede extraer de strateygy: strategy.compute_min_capital()
    REQ_CAPITAL = MIN_CAPITAL / LEVERAGE
    N_DAYS = (report.iloc[-1].close_date - report.iloc[0].open_date).total_seconds() / 86400
    start, end = report['open_date'].iloc[0], report['close_date'].iloc[-1]
    duration = report.iloc[-1].close_date - report.iloc[0].open_date
    pct_pnl = report.pnl_coinM.sum() / REQ_CAPITAL * 100
    daily_pct_pnl = pct_pnl / N_DAYS
    bh_return =round((report.close_price.iloc[-1] / report.open_price.iloc[0] - 1)*100,3) * LEVERAGE
    max_drawdown = report.pct_drawdown.apply(lambda x: float(str(x).replace('%', ''))).min()
    avg_drawdown = round(report.pct_drawdown.apply(lambda x: float(str(x).replace('%', ''))).mean(), 4)
    avg_so = round(report.num_safe_order.mean(), 2)
    max_so = report.num_safe_order.max()
    avg_deal_duration = (report.close_date - report.open_date).mean().total_seconds() / 86400 # seconds in a day
    max_deal_duration = (report.close_date - report.open_date).max().total_seconds() / 86400 # seconds in a day
    df = {'start': start, 'end': end, 'duration': duration,
          'leverage': str(LEVERAGE), 'pl_ret': round(pct_pnl,4),
          'bh_ret': bh_return, 'daily_pl_ret': round(daily_pct_pnl,4),
          'max_drawdown': max_drawdown, 'avg_drawdown':avg_drawdown,
          'avg_so': avg_so, 'max_so': max_so, 'num_deals': report.shape[0],
          'avg_deal_duration': round(avg_deal_duration, 2),
          'max_deal_duration': round(max_deal_duration, 2)}
    return pd.Series(df)