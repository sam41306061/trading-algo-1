import pandas as pd
import os
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# file location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, '../../', 'csv')

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

def calculate_stochastics(data, k_period=8, d_period=3):
    highest_high = data['High'].rolling(window=k_period).max()
    lowest_low = data['Low'].rolling(window=k_period).min()
    k = ((data['Close'] - lowest_low) / (highest_high - lowest_low)) * 40
    d = k.rolling(window=d_period).mean()
    return k , d


def plot_stochastics(data, k, d, symbol):
    # Normalize k and d to fall between 40 and 60
    k_normalized = ((k - k.min()) / (k.max() - k.min())) * 40 + 30
    d_normalized = ((d - d.min()) / (d.max() - d.min())) * 40 + 30

    # set initial figure 
    fig = make_subplots(rows=1, cols=1, shared_xaxes=True, vertical_spacing=0.1)
    
    # Add threshold lines
    fig.add_trace(go.Scatter(x=data.index, y=[40]*len(data.index), mode='lines', name='Oversold', line=dict(color='green', width=2, dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=[60]*len(data.index), mode='lines', name='Overbought', line=dict(color='red', width=2, dash='dash')))
    
    #k plot
    fig.add_trace(go.Scatter(x=data.index, y=k_normalized, mode='lines', name='%K', line=dict(color='blue', width=2)))
    #d plot
    fig.add_trace(go.Scatter(x=data.index, y=d_normalized, mode='lines', name='%D', line=dict(color='orange', width=2)))
    
    # update layout
    fig.update_layout(
        title=f"{symbol} Stochastics",
        xaxis_title='Date',
        yaxis_title='Stochastics',
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        yaxis=dict(range=[30, 70])  # Set y-axis range to focus on the middle areaX
    )
    fig.show()

if __name__ == '__main__':
    # Load data
    symbol = 'ALLE'
    data = get_stock_data_csv([symbol])
    k, d = calculate_stochastics(data[symbol])
    plot_stochastics(data[symbol], k, d, symbol)