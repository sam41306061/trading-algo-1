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


def calculate_ema(data, periods):
    df = data.copy()
    for period in periods:
        df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
    return df
   

if __name__ == "__main__":
    tickers = ['ALLE']
    data = get_stock_data_csv(tickers)

# calculate emas
periods = [8, 21, 34]
ema_data = calculate_ema(data[tickers[0]], periods)
print(ema_data)

# create subplots
fig = make_subplots(
    rows = 2, cols=1, shared_xaxes=True,
    vertical_spacing=0.02,
    row_heights=[0.7, 0.3],
    subplot_titles=('ALLE Price Chart with EMAs', 'Volume')
)

# #price chart with EMA's
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

# EMAs
for period in periods:
    fig.add_trace(
    go.Scatter(x=ema_data.index.strftime('%Y-%m-%d'),
     y=ema_data[f'EMA_{period}'], mode='lines', name=f'EMA {period}'), 
     row=1, col=1
     )

# Volume
fig.add_trace(go.Bar(x=ema_data.index.strftime('%Y-%m-%d'), y=ema_data['Volume']), row=2, col=1)

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

# Show the plot
fig.show()

# Print DataFrame structure for debugging
print(ema_data.columns)





#### Orignal idea that displays ######
#     # Calculate EMAs
#     periods = [8, 21, 34]
#     ema_data = calculate_ema(data[tickers[0]], periods)

#    # Plotting
#     fig, ax = plt.subplots(figsize=(12, 6))
#     # close
#     ax.plot(ema_data.index, ema_data['Close'], label='Close')
#     #ema
#     for i, period in enumerate(periods):
#         ax.plot(ema_data.index, ema_data[f'EMA_{period}'], label=f'EMA {period}')

#     # Set title and legend
#     ax.set_title('ALLE Price Chart with EMAs')
#     ax.legend()
#     ax.grid(True)

#     # Customize x-axis
#     ax.set_xlabel('Date')
#     ax.set_ylabel('Price')

#     # Adjust layout and show plot
#     plt.tight_layout()
#     plt.show()

#     # Print DataFrame structure for debugging
#     print(ema_data.columns)

   