import pandas as pd
import os
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# file location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, '..', 'csv')

# file location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, '..', 'csv')
# get the test data from the csv folder 
def get_stock_data_csv(tickers):
    data ={}
    for ticker in tickers: 
        try:
            # read csv file 
            csv_path = os.path.join(BASE_DIR, '..', 'csv', f"{ticker}.csv")
            df = pd.read_csv(csv_path, parse_dates=['Date'])
            df.set_index('Date', inplace= True)
            data[ticker] = df

        except Exception as e:
            print(f"Error reading {ticker}.csv, Error:{e}")
            print(f"File not found: {df}")
        
    return data

def calculate_ema(data, ema_periods):
    df = data.copy()
    for period in ema_periods:
        df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
    return df

def calculate_sma(data, sma_periods):
    df = data.copy()
    for period in sma_periods:
        df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
    return df

def plot_ema_and_sma(data, ema_periods, sma_periods):
    # Calculate EMAs
    ema_data = calculate_ema(data[tickers[0]], ema_periods)
    print(ema_data)

    # Calculate SMAs
    sma_data = calculate_sma(data[tickers[0]], sma_periods)
    print(sma_data)

    # Create subplots
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.7, 0.3],
        subplot_titles=('ALLE Price Chart with EMAs and SMAs', 'Volume')
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

    # Volume
    fig.add_trace(
        go.Bar(x=ema_data.index.strftime('%Y-%m-%d'), 
               y=ema_data['Volume']),
        row=2, col=1
    )

    # Update layout
    fig.update_layout(
        title=f"{tickers[0]} Stock Analysis",
        xaxis=dict(
            rangeslider=dict(visible=False),
            type="date",
            tickformat="%Y-%m-%d"
        ),
        xaxis2_title="Date",
        yaxis1_title="Price",
        yaxis2_title="Volume",
        height=800,
        showlegend=True
    )
    
    fig.show()



if __name__ == "__main__":
    tickers = ['ALLE']
    data = get_stock_data_csv(tickers)
    ema_periods = [8, 21, 34]
    sma_periods = [100, 200]
    plot_ema_and_sma(data, ema_periods, sma_periods)
    print(data)