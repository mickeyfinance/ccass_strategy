from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import pandas as pd
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import yfinance as yf

# Import the backtrader platform
import backtrader as bt

# Download data from Yfinance
stocks = pd.read_excel('/Users/mickeylau/Desktop/Big project/ListOfSecurities.xlsx', usecols=[0], skiprows=2)
start = datetime.date(2022,3,5)
end = datetime.datetime.today()


yfinance_data = {}

for ticker in stocks['Stock Code']:
    ticker = str(ticker).zfill(4)+".HK"
    temp = yf.download(ticker, start, end)
    temp.index = pd.to_datetime(temp.index)
    yfinance_data[ticker] = temp

# Create a Stratey
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])


if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Create a Data Feed



    data = bt.feeds.PandasData(
        dataname=yfinance_data[0],
        # Do not pass values before this date
        fromdate=datetime.datetime(2022, 3, 7),
        # Do not pass values before this date
        todate=datetime.datetime(2022, 12, 31),
        # Do not pass values after this date
        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())