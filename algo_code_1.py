import pandas as pd
import numpy as np
import sys
from datetime import datetime, timedelta

class ADXBacktester:
    def __init__(self, csv_file, period=14, adx_threshold=25, max_holding_days=2):
        self.csv_file = csv_file
        self.period = period
        self.adx_threshold = adx_threshold
        self.max_holding_days = max_holding_days
        self.data = None
        self.trades = []
        
    def load_data(self):
        try:
            self.data = pd.read_csv(self.csv_file)
            columns_map = {}
            for col in self.data.columns:
                col_lower = col.lower().strip()
                if 'date' in col_lower:
                    columns_map[col] = 'date'
                elif 'time' in col_lower:
                    columns_map[col] = 'time'
                elif col_lower in ['open', 'o']:
                    columns_map[col] = 'open'
                elif col_lower in ['high', 'h']:
                    columns_map[col] = 'high'
                elif col_lower in ['low', 'l']:
                    columns_map[col] = 'low'
                elif col_lower in ['close', 'c']:
                    columns_map[col] = 'close' 
                elif col_lower in ['volume', 'vol', 'v']:
                    columns_map[col] = 'volume'

            self.data.rename(columns=columns_map, inplace=True)
            
            if 'time' in self.data.columns:
                self.data['datetime'] = pd.to_datetime(self.data['date'].astype(str) + ' ' + self.data['time'].astype(str))
            else:
                try:
                    self.data['datetime'] = pd.to_datetime(self.data['date'])
                except:
                    try:
                        self.data['datetime'] = pd.to_datetime(self.data['date'], dayfirst=True)
                    except:
                        self.data['datetime'] = pd.to_datetime(self.data['date'])
            
            self.data.sort_values('datetime', inplace=True)
            self.data.reset_index(drop=True, inplace=True)
            
            self.data['price'] = self.data['close']
            return True 
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def calculate_adx(self):
        high = self.data['high'].values
        low = self.data['low'].values
        close = self.data['close'].values
        n = len(self.data)
        TR = np.zeros(n)
        plus_DM = np.zeros(n)
        minus_DM = np.zeros(n)
        for i in range(1, n):
            TR[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
            up_move = high[i] - high[i-1]
            down_move = low[i-1] - low[i]
            
            if up_move > down_move and up_move > 0:
                plus_DM[i] = up_move
            else:
                plus_DM[i] = 0
                
            if down_move > up_move and down_move > 0:
                minus_DM[i] = down_move
            else:
                minus_DM[i] = 0
        ATR = np.zeros(n)
        plus_DM_smooth = np.zeros(n)
        minus_DM_smooth = np.zeros(n)
        start_idx = self.period
        if start_idx < n:
            ATR[start_idx] = np.mean(TR[1:start_idx+1])
            plus_DM_smooth[start_idx] = np.mean(plus_DM[1:start_idx+1])
            minus_DM_smooth[start_idx] = np.mean(minus_DM[1:start_idx+1])
            for i in range(start_idx + 1, n):
                ATR[i] = (ATR[i-1] * (self.period - 1) + TR[i]) / self.period
                plus_DM_smooth[i] = (plus_DM_smooth[i-1] * (self.period - 1) + plus_DM[i]) / self.period
                minus_DM_smooth[i] = (minus_DM_smooth[i-1] * (self.period - 1) + minus_DM[i]) / self.period
        plus_DI = np.zeros(n)
        minus_DI = np.zeros(n)
        
        for i in range(start_idx, n):
            if ATR[i] != 0:
                plus_DI[i] = (plus_DM_smooth[i] / ATR[i]) * 100
                minus_DI[i] = (minus_DM_smooth[i] / ATR[i]) * 100
        DX = np.zeros(n)
        for i in range(start_idx, n):
            di_sum = plus_DI[i] + minus_DI[i]
            if di_sum != 0:
                DX[i] = abs(plus_DI[i] - minus_DI[i]) / di_sum * 100
        ADX = np.zeros(n)
        adx_start = start_idx + self.period - 1
        if adx_start < n:
            ADX[adx_start] = np.mean(DX[start_idx:adx_start+1])
            
            for i in range(adx_start + 1, n):
                ADX[i] = (ADX[i-1] * (self.period - 1) + DX[i]) / self.period
        self.data['ADX'] = ADX
        self.data['+DI'] = plus_DI
        self.data['-DI'] = minus_DI
        self.data['price_change'] = self.data['price'].pct_change()
        self.data['volatility'] = self.data['price_change'].rolling(5).std()
    
    def backtest_strategy(self):
        position = None
        entry_price = 0
        entry_datetime = None
        entry_idx = 0
        for i in range(self.period, len(self.data)):
            current_datetime = self.data.loc[i, 'datetime']
            current_price = self.data.loc[i, 'price']
            adx_val = self.data.loc[i, 'ADX']
            plus_di = self.data.loc[i, '+DI']
            minus_di = self.data.loc[i, '-DI']
            if adx_val == 0 or np.isnan(adx_val) or adx_val <= 20:
                continue
            if position is not None:
                intervals_held = i - entry_idx
                max_intervals = self.max_holding_days * 48
                
                if position == 'long':
                    current_profit_pct = (current_price - entry_price) / entry_price * 100
                else:
                    current_profit_pct = (entry_price - current_price) / entry_price * 100
                should_exit = False
                if intervals_held >= max_intervals:
                    should_exit = True
                else:
                    if current_profit_pct >= 1.5 and adx_val <= self.data.loc[entry_idx, 'ADX'] * 0.85:
                        should_exit = True
                    elif current_profit_pct <= -0.5 and adx_val <= self.data.loc[entry_idx, 'ADX'] * 0.85:
                        should_exit = True
                
                if should_exit:
                    if position == 'long':
                        profit_pct = (current_price - entry_price) / entry_price * 100
                    else:
                        profit_pct = (entry_price - current_price) / entry_price * 100
                    
                    self.trades.append({
                        'entry_datetime': entry_datetime,
                        'exit_datetime': current_datetime,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'position': position,
                        'profit_pct': profit_pct,
                        'intervals_held': intervals_held,
                        'adx_entry': self.data.loc[entry_idx, 'ADX'],
                        'adx_exit': adx_val,
                    })
                    
                    position = None
            if position is None and adx_val >= self.adx_threshold:
                di_difference = abs(plus_di - minus_di)
                volatility = self.data.loc[i, 'volatility'] if not pd.isna(self.data.loc[i, 'volatility']) else 0.02
                
                if di_difference >= 30 and volatility <= 0.05:  
                    if (plus_di > minus_di and plus_di >= 40 and 
                        plus_di > self.data.loc[i-1, '+DI']):  
                        recent_trend = (current_price - self.data.loc[i-3, 'price']) / self.data.loc[i-3, 'price']
                        if recent_trend >= -0.08: 
                            position = 'long'
                            entry_price = current_price
                            entry_datetime = current_datetime
                            entry_idx = i
                    elif (minus_di > plus_di and minus_di >= 40 and 
                          minus_di > self.data.loc[i-1, '-DI']): 
                        recent_trend = (current_price - self.data.loc[i-3, 'price']) / self.data.loc[i-3, 'price']
                        if recent_trend <= 0.08:  
                            position = 'short'
                            entry_price = current_price
                            entry_datetime = current_datetime
                            entry_idx = i
        
        if position is not None:
            final_idx = len(self.data) - 1
            final_price = self.data.iloc[final_idx]['price']
            final_datetime = self.data.iloc[final_idx]['datetime']
            final_intervals = final_idx - entry_idx
            
            if position == 'long':
                profit_pct = (final_price - entry_price) / entry_price * 100
            else:
                profit_pct = (entry_price - final_price) / entry_price * 100
            
            self.trades.append({
                'entry_datetime': entry_datetime,
                'exit_datetime': final_datetime,
                'entry_price': entry_price,
                'exit_price': final_price,
                'position': position,
                'profit_pct': profit_pct,
                'intervals_held': final_intervals,
                'adx_entry': self.data.loc[entry_idx, 'ADX'],
                'adx_exit': self.data.iloc[final_idx]['ADX']
            })
    
    def calculate_performance_metrics(self):
        if len(self.trades) == 0:
            print("No trades executed!")
            return None     
        trades_df = pd.DataFrame(self.trades)
        num_trades = len(trades_df)
        total_profit_pct = trades_df['profit_pct'].sum()
        winning_trades = trades_df[trades_df['profit_pct'] > 0]
        win_rate = len(winning_trades) / num_trades * 100
        
        results = {
            'num_trades': num_trades,
            'total_profit_pct': total_profit_pct,
            'win_rate': win_rate
        }
        
        return results
    
    def run_backtest(self):
        if not self.load_data():
            return None
        self.calculate_adx()
        self.backtest_strategy()
        results = self.calculate_performance_metrics()
        
        if results is None:
            return None
        
        print(f"Number of Trades: {results['num_trades']}")
        print(f"Total Profit %: {results['total_profit_pct']:.2f}%")
        print(f"Win Rate: {results['win_rate']:.1f}%")
        
        return results

def main():
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        print("No CSV file provided.")
        exit(1)
    backtester = ADXBacktester(csv_file, adx_threshold=25)  
    results = backtester.run_backtest()
if __name__ == "__main__":
    main()
