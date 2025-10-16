#This app is used to automatically calculate a rough beta of inputted companies using SPY returns. Can be used for quick comparisons between companies.

# import necessary libraries
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.express as px

#streamlit page configuration
st.set_page_config(
    page_title="Comparing Company Returns")

st.title("Comparing Company Returns")
st.write("Application by Jodon Montgomery")
st.markdown("---")
st.markdown(
    '<span style="color: green;">Calculates the rough beta of inputted companies, compared to the S&P 500 (SPY).</span>',
    unsafe_allow_html=True,
)

time_periods = ['5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', '20y', 'ytd', 'max'] # Valid time periods used for calculations
default_time_period = '10y'#sets default list selection to 10Y
selected_time_period = st.selectbox("Select Time Period:", time_periods, index=time_periods.index(default_time_period))

def get_historical_data(ticker): #Pulls closing data from yahoo finance. Multiple possible error messages.
    try:
        if not ticker:
            return None
        stock_data = yf.download(ticker, period=selected_time_period, auto_adjust=False) #can change time period here
        if stock_data.empty:
            st.error(f"No data available for {ticker}. Please enter a valid ticker.")
            return None
        elif 'Adj Close' in stock_data.columns:
            return stock_data['Adj Close'] #returns adjusted closing prices for inputted stock
        else:
            st.error(f"Data for {ticker} is not available.")
            return None
    except Exception as e:
        st.error(f"An error occurred while fetching data for {ticker}")
        return None

def calculate_average_annual_return(ticker2): #uses log returns of daily stock price changes to get average daily return. Multiplies by number of trading days to get average annual return. 
    closing_prices = get_historical_data(ticker2)
    if closing_prices is None: #helps error codes to function
        return None
    log_returns = np.log(closing_prices / closing_prices.shift(1)).dropna() #log returns of daily price changes
    average_daily_return = log_returns.mean() #average change in closing prices daily change
    average_annual_return = average_daily_return * 252 #annual rate is average daily change multiplied by trading days
    return average_annual_return * 100



def visualize_returns(tickers): #function creates a chart that shows stock price change
    fig = go.Figure()

    # Define a list of colors for each ticker. Avoids two of the same colors in a row
    line_colors = ['blue', 'red', 'green', 'orange', 'purple', 'yellow', 'cyan', 'magenta', 'brown', 'pink', 'gray', 'olive', 'teal']

    for i, ticker in enumerate(tickers):
        data = get_historical_data(ticker)
        if data is not None:
            # Set line color for each ticker
            color = line_colors[i % len(line_colors)]

            # Update the go.Scatter trace to include line color
            fig.add_trace(go.Scatter(x=data.index, y=data, mode='lines', name=ticker, line=dict(color=color)))

    fig.update_layout(title="Historical Adjusted Close Prices", xaxis_title="Date", yaxis_title="Adjusted Close Price")
    st.plotly_chart(fig, use_container_width=True)


def calculate_beta(ticker): #calculates beta by comparing stock data to SPY closing prices.
    try:
        if ticker == "SPY": #sets beta of SPY to 1.00 to avoid errors
            return 1.00
        
        stock_data = get_historical_data(ticker)
        if stock_data is None:
            return None
        
        spy_data = yf.download("SPY", period=selected_time_period, auto_adjust=False)['Adj Close']
        if spy_data.empty:
            st.error("No data available for SPY. Please check your internet connection.")
            return None

        merged_data = pd.merge(stock_data, spy_data, how='inner', left_index=True, right_index=True, suffixes=(f'_{ticker}', '_SPY'))

        log_returns_stock = np.log(merged_data[f'Adj Close_{ticker}'] / merged_data[f'Adj Close_{ticker}'].shift(1)).dropna()
        log_returns_spy = np.log(merged_data['Adj Close_SPY'] / merged_data['Adj Close_SPY'].shift(1)).dropna()

        slope, intercept = np.polyfit(log_returns_spy, log_returns_stock, 1)
        beta = slope

        return beta
    except Exception as e:
        st.error(f"An error occurred while calculating beta for {ticker}")
        return None

# Dynamic Ticker Input. 
tickers = []
while True:
    new_ticker = st.text_input("Enter Ticker (e.g. 'AAPL'):", key=len(tickers))
    if not new_ticker:
        break
    tickers.append(new_ticker)

#Initialize lists
valid_tickers = []
individual_returns = []
individual_betas = []

for ticker in tickers: 
    average_annual_return = calculate_average_annual_return(ticker)
    beta = calculate_beta(ticker)
    if average_annual_return is not None:
        annual_return = average_annual_return
        individual_returns.append(annual_return)
        valid_tickers.append(ticker)
    if beta is not None:
        if ticker != "SPY":
            individual_betas.append(beta)
            st.write(f"Beta for {ticker} is: {beta:.2f}")
        else:
            st.write("Beta for SPY is 1.00")
    else:
        st.write(f"")

#creates chart of returns
if individual_betas or "SPY" in valid_tickers:
    visualize_returns(valid_tickers)
else:
    st.write("No valid tickers entered. Please enter at least one valid ticker.")
