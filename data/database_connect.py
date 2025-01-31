import pandas as pd
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Get environment variables
DB_CONN = os.environ.get('DB_CONNECTION')

cluster = MongoClient(DB_CONN)
db = cluster["sector_historical_data"]
ticker_collection = db["ticker_data"]

def get_stock_data_sector(sector):
    data = {}

    # Step 1: Extract unique tickers for the given sector
    sector_tickers = ticker_collection.distinct("TickerSymbol", {"Sector": sector})
    print(f"Tickers in sector {sector}: {sector_tickers}")

    # Step 2: Fetch and process data for each ticker
    for ticker in sector_tickers:
        print(f"Processing ticker: {ticker}")

        try:
            #query to modify by date at some point
            ticker_data = list(
                ticker_collection.find({
                    "TickerSymbol": ticker,
                    "Sector": sector
                })
            )

            if ticker_data:
                # Convert data to a DataFrame
                df = pd.DataFrame(ticker_data)

                # Ensure the 'Date' column is a datetime object and set it as the index
                if 'Date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['Date']):
                    df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)

                # Sanitize and keep only relevant columns
                df = df[['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']]

                # Add the processed DataFrame to the result dictionary
                data[ticker] = df
                print(f"Successfully processed data for {ticker}")
            else:
                print(f"No data found for {ticker}")

        except Exception as e:
            print(f"Error processing data for {ticker}: {e}")

    return data

if __name__ == "__main__":
    sector = "HealthCare"
    data = get_stock_data_sector(sector)

for ticker, df in data.items():
    filename = f"{ticker}.csv"
    df.to_csv(f'../csv/HealthCare/{ticker}_data_his.csv')
    print(f"Saved data for {ticker} to {filename}")


