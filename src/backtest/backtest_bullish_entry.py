import pandas as pd
import os
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go


# File location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DATA_DIR = os.path.join(BASE_DIR, '../', 'csv')
#/Users/sam4130/Documents/GitHub/trading-algo-1/src/csv/HealthCare
#sector
sector = 'HealthCare'
tickers = [ "LLY", "UNH", "JNJ", "ABBV", "MRK", "ABT", "TMO", "ISRG", "AMGN", "DHR",
            "PFE", "SYK", "BSX", "BMY", "VRTX", "GILD", "MDT", "ELV", "CI", "ZTS",
            "MCK", "REGN", "CVS", "BDX", "HCA", "EW", "COR", "A", "GEHC", "RMD",
            "HUM", "IQV",] 

# Get the test data from the csv folder 
def get_stock_data_csv(tickers):
    data = {}
    for ticker in tickers:
        csv_path = os.path.join(ROOT_DATA_DIR, sector, f"{ticker}_data_his.csv")
        
        try:
            df = pd.read_csv(csv_path, parse_dates=['Date'])
            df.set_index('Date', inplace=True)
            data[ticker] = df
        except Exception as e:
            print(f"Error reading {ticker}.csv, Error:{e}")
            print(f"File not found: {csv_path}")
    
    return data


def calculate_ema(data, ema_periods):
    """
    Function to Calculate Exponential Moving Averages
    """
    df = data.copy()
    for period in ema_periods:
        df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
    return df


def calculate_sma(data, sma_periods):
    """
    Function to Calculate Simple Moving Averages
    """
    df = data.copy()
    for period in sma_periods:
        df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
    return df

def calculate_rsi(data, rsi_period=2):
    """
    Function to calculate RSI with settings matching ThinkorSwim:
    - RSI length: 2
    - Average Type: Wilder's (handled by EWM)
    """
    df = data
    df['change']  = df['Close'] - df['Close'].shift(1)
    df['gain'] = np.where(df['change'] >= 0, df['change'], 0)
    df['loss'] = np.where(df['change'] < 0, -1 * df['change'], 0)
    
    #Initialize avg_gain and avg_loss
    df['avg_gain'] = 0.0
    df['avg_loss'] = 0.0

    # Calculate the initial average gain and loss
    df.loc[df.index[rsi_period], 'avg_gain'] = df['gain'].rolling(window=rsi_period).mean().iloc[rsi_period]
    df.loc[df.index[rsi_period], 'avg_loss'] = df['loss'].rolling(window=rsi_period).mean().iloc[rsi_period]

   # Apply Wilder's smoothing
    for i in range(rsi_period + 1, len(df)):
        df.loc[df.index[i], 'avg_gain'] = (df.loc[df.index[i-1], 'avg_gain'] * (rsi_period - 1) + df.loc[df.index[i], 'gain']) / rsi_period
        df.loc[df.index[i], 'avg_loss'] = (df.loc[df.index[i-1], 'avg_loss'] * (rsi_period - 1) + df.loc[df.index[i], 'loss']) / rsi_period
    
    df['rs'] = df['avg_gain'] / df['avg_loss']
    df['rsi'] = 100 - (100 / (1 + df['rs']))
    df.dropna()

    return df['rsi']

def calculate_stochastics(data, k_period=8, d_period=3):
    """
    Function to Calculate Stochastics
    - k_period: 8
    - d_period: 3
    """
    highest_high = data['High'].rolling(window=k_period).max()
    lowest_low = data['Low'].rolling(window=k_period).min()
    k = ((data['Close'] - lowest_low) / (highest_high - lowest_low))
    d = k.rolling(window=d_period).mean()
    return pd.DataFrame({'%K': k, '%D': d})

def bullish_strategy(data):
    """
    Function to apply the bullish strategy
    - EMA: 8, 21, 34
    - SMA: 100, 200
    - RSI: 2 day period
    - Stochastics: 8, 3

    """
    # Think about how to optimize the strategy for different entry points, 8 vs 21 vs 34 vs 50
    # Calculate EMAs and SMAs
    for ticker in data:
        df = data[ticker]

        df = calculate_ema(df, [8, 21, 34])
        df = calculate_sma(df, [50,100, 200])

        # RSI
        bullish_rsi = calculate_rsi(df)
        # Stochastics
        bullish_stochas = calculate_stochastics(df)

        ema_sma_trend_mask = (
            (df['EMA_8'] > df['EMA_21']) &
            (df['EMA_21'] > df['EMA_34']) &
            (df['SMA_50'] > df['SMA_100']) &
            (df['SMA_100'] > df['SMA_200'])
        )
        retracement_stochas_mask = (bullish_stochas['%K'] <= 40) & (bullish_stochas['%D'] <= 40)
        retracement_rsi_mask = bullish_rsi <= 10
        low_bar_mask = df['Adj Close'] > df['Low']

        single_mask =  ema_sma_trend_mask & retracement_stochas_mask & retracement_rsi_mask  & low_bar_mask
         # Need to research a weighted structure algo in order to determine an optimal entry point but not all requierments are met
        df['Entry Point'] = np.where(single_mask, 1, 0)
        df = df.dropna()
        data[ticker] = df
        
    return data

def evaluate_strategy(data):
    """
    Function to evaluate the strategy
    """
    entry_points = []
    comms = 0.008  # 0.8% commission fee
    inital_balance = 5000
    drawdown_threshold = -0.10
    max_hold_days = 14  # max 14 day holding period
    total_reinvested = 0

    for ticker in data:
        df = data[ticker]
        
        # Find entry points
        entries = df[df['Entry Point'] == 1].copy()
        
        # Calculate PNLs
        entries['PNL'] = np.nan
        entries['End date'] = pd.NaT

        # Initalize tracking
        entries['Position'] = 0
        entries['Start Price'] = None
        entries ['Stop Loss'] = None


        for i, row in entries.iterrows():
            start_price = row['Adj Close']
            start_index = df.index.get_loc(i)
            
            # Find the best PNL in a 14 day window
            max_pnl = -999 #ludicrously low so it always gets overwritten
            stop_loss = None

             # check if there is a trade being identified at the end of the dataset
            if start_index + max_hold_days >= len(df):
                max_hold_days = len(df) - start_index - 1

            
            for end_index in range(start_index + 1, start_index + max_hold_days + 1):
                end_price = df.iloc[end_index]['Adj Close']
                pnl = (end_price - start_price) / start_price - comms
                if pnl > max_pnl:
                    max_pnl = pnl
                    max_end_date = df.index[end_index]

                    #Check stop loss 
                    if abs(pnl) > drawdown_threshold * start_price:
                        stop_loss = end_price
                        break

            entries.at[i, 'PNL'] = max_pnl
            entries.at[i, 'End date'] = max_end_date

            #Manage Position
            if max_pnl > 0: 
                entries.at[i, 'Position'] = 1
                entries.at[i, 'Start Price'] = start_price
                entries.at[i, 'Stop Loss'] = stop_loss
            else:
                entries.at[i, 'Position'] = 0

            print(f"Entry date: {i}, PNL: {entries.at[i, 'PNL']}, End date: {entries.at[i, 'End date']}")
        
        #Reinvest winnings
        for i, row in entries.iterrows():
            if row['PNL'] > 0 and row['Position'] == 1:
                reinvest_amount = row['PNL'] * inital_balance
                inital_balance += reinvest_amount
                total_reinvested += reinvest_amount
                entries.at[i, 'Reinvested Amount'] = reinvest_amount
                entries.at[i, 'Total Amount'] = inital_balance
                print(f"Reinvested ${reinvest_amount:.2f} at entry: {i} for {ticker}")

        # Check if 'Date' column exists, if not, use the index as Date
        if 'Date' not in entries.columns:
            entries['Date'] = entries.index

        # Select the desired columns
        ticker_entry_points = entries[['Date', 'Entry Point', 'Adj Close', 'PNL', 'End date', 'Position', 'Start Price', 'Stop Loss']]
        entry_points.append((ticker, ticker_entry_points))
        print(f"Total reinvested amount: ${total_reinvested:.2f} for {ticker}")
    
    return entry_points, inital_balance

def plot_ema_sma_strategy(data, ema_periods, sma_periods, ticker):
    # calculate EMAs
    ema_data = calculate_ema(data[ticker], ema_periods)

    sma_data = calculate_sma(data[ticker], [100, 200])

    stochastics_data = calculate_stochastics(data[ticker])
    k = stochastics_data['%K']
    d = stochastics_data['%D']

    # Normalize k and d
    k_normalized = ((k - k.min()) / (k.max() - k.min())) * 40 + 30
    d_normalized = ((d - d.min()) / (d.max() - d.min())) * 40 + 30
    
     # RSI
    bullish_rsi = calculate_rsi(data[ticker])
    rsi_normalized = ((bullish_rsi - bullish_rsi.min()) / (bullish_rsi.max() - bullish_rsi.min())) * 40 + 30

     # Create subplots
    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.4, 0.1, 0.1, 0.1],
        subplot_titles=(f'{ticker} Price Chart with EMAs and SMAs', 'RSI', 'Stochastics', 'Volume')
    )

     # Price chart with candlesticks
    fig.add_trace(
        go.Candlestick(
            x=ema_data.index.strftime('%Y-%m-%d'),
            open=ema_data['Open'],
            high=ema_data['High'],
            low=ema_data['Low'],
            close=ema_data['Close'],
            name='Price'
        ),
        row=1, col=1
    )

     # Process EMAs
    for period in ema_periods:
        fig.add_trace(
            go.Scatter(
                x=ema_data.index.strftime('%Y-%m-%d'),
                y=ema_data[f'EMA_{period}'],
                name=f'EMA_{period}'
            ),
            row=1, col=1
        )
      # Process SMAs
    for period in sma_periods:
        fig.add_trace(
            go.Scatter(
                x=sma_data.index.strftime('%Y-%m-%d'),
                y=sma_data[f'SMA_{period}'],
                name=f'SMA_{period}'
            ),
            row=1, col=1
        )

     # Plot entry points
    entry_points = data[ticker][data[ticker]['Entry Point'] == 1]
    fig.add_trace(
        go.Scatter(
            x=entry_points.index,
            y=entry_points['Close'],
            mode='markers',
            marker=dict(color='green', size=8),
            name='Entry Points'
        ),
        row=1, col=1
    )

    # RSI
    fig.add_trace(go.Scatter(x=data[tickers[0]].index, y=rsi_normalized, mode='lines',line=dict(color='blue'),name='RSI'), row=2, col=1)
    fig.add_trace(go.Scatter(x=data[tickers[0]].index, y=[70] * len(data), mode='lines', line=dict(dash='dash', color='red'), name='Overbought'),row=2, col=1)
    fig.add_trace(go.Scatter(x=data[tickers[0]].index, y=[30] * len(data), mode='lines', line=dict(dash='dash', color='green'), name='Oversold'),row=2, col=1)
    

    # Stochastics
    stochastics_data = pd.DataFrame({'%K': k_normalized, '%D': d_normalized})
    fig.add_trace(go.Scatter(x=data[ticker].index, y=stochastics_data['%K'], mode='lines', name='%K', line=dict(color='blue', width=2)), row=3, col=1)
    fig.add_trace(go.Scatter(x=data[ticker].index, y=stochastics_data['%D'], mode='lines', name='%D', line=dict(color='orange', width=2)), row=3, col=1)
    fig.add_trace(go.Scatter(x=data[ticker].index, y=[40]*len(data[ticker].index), mode='lines', name='Oversold', line=dict(color='green', width=2, dash='dash')), row=3, col=1)
    fig.add_trace(go.Scatter(x=data[ticker].index, y=[60]*len(data[ticker].index), mode='lines', name='Overbought', line=dict(color='red', width=2, dash='dash')), row=3, col=1)

    # Volume
    fig.add_trace(
        go.Bar(x=ema_data.index.strftime('%Y-%m-%d'), 
               y=ema_data['Volume']),
        row=4, col=1
    )

     # Update layout
    fig.update_layout(
        title=f"{ticker} Stock Analysis",
        xaxis=dict(
            rangeslider=dict(visible=False),
            type="date",
            tickformat="%Y-%m-%d"
        ),
        xaxis2_title="Date",
        yaxis1_title="Price",
        yaxis2_title="Indicators",
        height=900,
        showlegend=True
    )
    
    fig.show()

if __name__ == "__main__":
    ema_periods = [8, 21, 34]
    sma_periods = [50,100, 200]
    data = get_stock_data_csv(tickers)
    data = bullish_strategy(data)
    entry_points,inital_balance = evaluate_strategy(data)



 # Plot strategy for each ticker
    for ticker in tickers:
        if ticker in data:
            df = data[ticker]
            if df['Entry Point'].sum() > 3:
                plot_ema_sma_strategy(data, ema_periods, sma_periods, ticker)
            else:
                print(f"Skipping plot for {ticker} as no valid entry points were found.")
        else:
            print(f"{ticker} did not have any valid data.")

# Export results for each ticker

    for ticker, ticker_entry_points in entry_points:
        #testing purposes
        print(f"\nWriting CSV for {ticker}:")
        print(f"Number of rows: {len(ticker_entry_points)}")
        print(f"Number of entry points: {ticker_entry_points['Entry Point'].sum()}")

        if not ticker_entry_points.empty:
            ticker_entry_points.to_csv(f'{ticker}_results.csv', index=False)
            print(f"Results exported for {ticker}")
        else:
            print(f"No valid entry points found for {ticker}")
