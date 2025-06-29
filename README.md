Introduction:
This repository contains an ADX-based short-term trading strategy implemented in Python. 
The strategy is built around identifying strong directional trends using the Average Directional Index (ADX) indicator, and entering trades only when specific technical and market conditions are met. 
This readme explains the strategy logic, indicator math, coding structure etc.



Things learnt while doing the project:

Understanding how stock market works and what is algorithmic trading.

Understanding of ADX as a trend strength indicator.

How to compute +DI, -DI, and ADX values from raw data.

Filtering trades using volatility, DI strength, and ADX thresholds, for better returns using the strategy.

Short-term (here 2 days) position management using fixed holding periods and risk-based exits.

Creating a fully automated backtesting framework which takes in properly formatted csv data files from yfinance (python) and then processes accordingly.

Evaluating strategy performance using trade statistics (win rate, number of trades executed, net profit etc.)


About ADX (the indicator used in my strategy):

The Average Directional Index (ADX) is a technical indicator that measures how strong a trend is, without caring about its direction. 
It ranges from 0 to 100 as per the situation, i.e.
a low ADX (below 20) suggests a weak trend or sideways market where as
a high ADX (above 25–30) confirms a strong trend, maybe up or down.
To determine direction, we pair ADX with directional indicator:
+DI (Positive Directional Indicator): Indicates upward movement strength and
−DI (Negative Directional Indicator): Indicates downward movement strength.
This combination helps us avoid entering trades during directionless periods and instead focus only when the market is trending clearly, and also inn the correct direction for profit.

ADX calculation:
The code computes ADX manually, step-by-step, based on the standard Wilder’s method:

True Range (TR) = largest of: (Current high − current low), |Current high − previous close|, |Current low − previous close|.

+DM and −DM are calculated based on today's vs yesterday's highs and lows: If up move > down move and positive +DM implies up move, but if down move > up move and positive −DM implies down move.

+DI = 100 × (smoothed +DM / smoothed TR)

−DI = 100 × (smoothed −DM / smoothed TR)

DX = 100 × |+DI − −DI| / (+DI + −DI)

ADX is smoothed average of DX over time.

Strategy:
For getting heallthy profit, and other requirements like good win rate, fair number of trades etc. we try to build effective strategy using out ADX indicator.

Entry Conditions:

ADX must be above a threshold (here 30), signaling strong trend.

The difference between +DI and −DI must be large (here more than 12), indicating clear direction.

Volatility should be low (here under 3%) to avoid noisy markets.

Directional strength must be increasing. (e.g., +DI today > +DI yesterday)

Exit Conditions:

Trades are closed after 2 trading days max.

If trade is profitable (>0.5%) after 1 day and ADX weakens implies exit early to secure gains.

If trade is down more than 2% exit to stop loss to minimize loss.

Trade Tracking:
Every trade is logged with entry and exit dates, prices and profit percentages, days held, ADX on entry and exit etc.

Conclusion:
ADX is a fair enough indicator which can give nice results if used properly.
I have tested my code on many data sets and most of the results seemed to fulfil all the requirements.
This is why I can conclude ADX to be good indicator when used with proper directional analysis for correct sell and buy states.

Results obtained on backtesting (last 60 days data with candles of 15 minutes):

DIVISLAB.NS : Number of trades = 15, Win Rate = 80%, Net Profit = 5.62%

ETERNAL.NS : Number of trades = 40, Win Rate = 92.5%, Net Profit = 16.62%

FIRSTCRY.NS : Number of trades = 38, Win Rate = 84.2%, Net Profit = 29.34%

VBL.NS : Number of trades = 30, Win Rate = 86.7%, Net Profit = 10.56%

TRENT.NS : Number of trades = 33, Win Rate = 93.9%, Net Profit = 16.50%

TCS.NS : Number of trades = 10, Win Rate = 100%, Net Profit = 4.17%

SBIN.NS : Number of trades = 6, Win Rate = 100%, Net Profit = 3.09%

BAJFINANCE.NS : Number of trades = 25, Win Rate = 96%, Net Profit = 11.14%
