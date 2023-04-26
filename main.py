#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 28 22:49:54 2023

@author: mickeylau
"""

from screener import stock_filter
import pandas as pd
import os
import backtrader as bt
import datetime as datetime
import yfinance as yf
import backtrader.analyzers as btanalyzers
from backtrader.analyzers import SharpeRatio

################



# Create a Strategy class for backtest
class MyStrategy(bt.Strategy):

    params = (
            ('exitbars',10), ## Assume hold the stock for 10 days after buy
        )    
    def __init__(self):
        self.backtest_list = backtest_list
        self.bar_executed = {key: 0 for key in range(len(self.backtest_list))}
        
        self.lowest_lows = {}
        for i, d in enumerate(self.datas):
            
            self.lowest_lows[i] = bt.indicators.Lowest(self.datas[i],period = low_history_days)
        
    
    def next(self):
        i=0
        for ticker, backtest_dates in self.backtest_list:
            cur_date = self.data.datetime.date()
            #cur_date = datetime.datetime.strptime(str(cur_date),"%Y-%m-%d")
            
            #check if today dates is in backtest dates
            if cur_date in backtest_dates:
                
                # Criteria 1 for stock price: larger than 50 low
                Criteria1 = (self.datas[i].close[0]>self.lowest_lows[i][0])
                
                if Criteria1:
                    self.log("Buy Create {}".format(self.datas[i]))
                    
                    # Calculate how many shares we can buy with certain percentage of cash in portfolio 
                    cash = self.broker.get_cash()
                    target_value = size_stake * cash 
                    price = self.datas[i].close[0]
                    size = int(target_value / price)
                    
                    self.buy(self.datas[i], size=size)
                    self.bar_executed[i] = len(self)
                    #print(len(self), i, len(self.datas[i]),ticker, cur_date, backtest_dates)
            
            
            if self.bar_executed[i]>0:
                # hold for "exit_bar" number of days and sell
                if len(self) >= (self.bar_executed[i] +self.params.exitbars):
                    self.log("Sell create {}".format(self.datas[i]))
                    self.close(self.datas[i])
                    self.bar_executed[i]=0
                    #print(len(self), i, len(self.datas[i]),ticker, cur_date, backtest_dates)
            i+=1
            
            
    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print("{} {}".format(dt.isoformat(),txt))
        



def backtesting(backtest_list, start_date, end_date, init_cash, broker_com):
      
    cerebro = bt.Cerebro()

    
    if backtest_list:
        for ticker,backtest_dates in backtest_list:
            temp = bt.feeds.PandasData(dataname=yf.download(str(int(ticker)).zfill(4)+'.HK', start_date, end_date, auto_adjust=True))
            cerebro.adddata(temp)
        
        
    cerebro.addsizer(bt.sizers.SizerFix, stake=100)
    
    cerebro.addstrategy(MyStrategy)
    cerebro.addanalyzer(SharpeRatio, _name='mysharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio)
    cerebro.broker.setcash(init_cash)
    cerebro.broker.setcommission(commission = broker_com)
    print("Start portfolio {}".format(cerebro.broker.getvalue()))
    thestrats = cerebro.run()
    
    print("FInal Portfolio {}".format(cerebro.broker.getvalue()))
    thestrat = thestrats[0]
    #print(thestrat.analyzers.mysharpe.get_analysis())
    for each in thestrat.analyzers:
        each.print()
        
    cerebro.plot()  #plotting might have error, need install matplotlib==3.2.2
    
    return True
    
    
if __name__ == '__main__':
    # Set Hyper parameters here
    broker_holding_change = 0.05 #Criteria 1: check if broker change more than a certain percentage in ccass
    concentration_crit = 0.5 # Criteria 3: check if concentration in ccass is higher than this threshold
    low_history_days = 50 # Check if current price is higher than 50 low
    start_date=datetime.date(2021, 3, 8) #start date should be the earliest of the backtest dates
    end_date = datetime.date(2022,4,8)  
    broker_com = 0.001 
    init_cash = 1000000
    size_stake = 0.2 #Assume we use 29% cash to buy a new stock
    
    ###############
    
    # Download the sample data csv from dropbox.
    ccass_df = pd.read_csv("https://www.dropbox.com/s/cugbdibyys79orb/sample_data.csv?dl=1", parse_dates= ["record_date"])
    # Get the classification of the brokers, either Retail, Institution, or unknown
    broker_type = pd.read_csv(os.getcwd()+'/data/brokers.csv')
    # convert the date_time column to datetime object
    ccass_df['record_date'] = pd.to_datetime(ccass_df['record_date'])
    ccass_df['record_date'] = ccass_df['record_date'].dt.date
    ccass_df = pd.merge(ccass_df, broker_type, how="left", on=["participant_name"]).fillna("unknown")
    # Obtain a list of unique stock codes in the database.
    stock_list = ccass_df['stock_code'].unique()
    ##########
    
    backtest_list=[]
    
    for stock in stock_list:
        # Loop the stock list in the database, call the stock_filter function to check the dates that satisfy the requirements.
        df = ccass_df[ccass_df['stock_code']==stock]
        df = df.drop_duplicates(subset = ['record_date','participant_name'])
        screen_input = df.pivot(index = 'record_date', columns = 'participant_name', values = 'percent').fillna(0)
        pivot_bytype = df.pivot_table(index='record_date',columns='participant_type',values='percent',aggfunc='sum').fillna(0)
        screen_input = screen_input.join(pivot_bytype).fillna(0)
        filter_result = stock_filter(screen_input, broker_holding_change, concentration_crit)
        if any(filter_result):
            # Record the stock and dates that satisfy the requirements.
            backtest_list.append([stock, filter_result.index[filter_result].tolist()])
       
    backtesting(backtest_list, start_date, end_date, init_cash, broker_com)
        
