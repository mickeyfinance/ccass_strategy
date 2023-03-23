#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 17:27:44 2023

@author: mickeylau
"""


import mysql.connector
import pandas as pd
import os


##############
def stock_filter(df):
    broker_change = pd.DataFrame()
    for column in df.columns:
        broker_change['{}_change'.format(column)]= df[column].diff().fillna(0)
    
    # Criteria 1: big change/move in 1 broker/sum(all brokers)
    Criteria1 = (abs(broker_change) > 0.05)
    df["Criteria1"] = Criteria1.any(axis='columns')
    

    # Criteria 2: stock price change in past 1 month < 20% (i.e. no big up in the past)
   
    df['Criteria2'] = (Criteria1.any(axis='columns'))

    # Criteria 3: concentration - top 3 brokers occupy 70% of ccass
    df['Criteria3'] = Criteria1.any(axis='columns')
    
    df['Fullfilment'] = df[['Criteria1','Criteria2','Criteria3']].all(axis='columns')
 
    
    return (df['Fullfilment'])
#############


"""
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="91692388",
  database="ccass_data"
)
mycursor = mydb.cursor()
stock_list = mycursor.execute("SELECT DISTINCT stock_code FROM holdings")
stock_list = mycursor.fetchall()
"""
##########
#ccass_df = pd.read_json(os.getcwd()+'/data/sample_data.json', convert_dates=['record_date'])
ccass_df = pd.read_csv(os.getcwd()+'/data/sample_data.csv',parse_dates= ["record_date"])
# convert the date_time column to datetime object
ccass_df['record_date'] = pd.to_datetime(ccass_df['record_date'])
ccass_df['record_date'] = ccass_df['record_date'].dt.date
stock_list = ccass_df['stock_code'].unique()
##########

backtest_list=[]

for stock in stock_list:
    df = ccass_df[ccass_df['stock_code']==stock]
    df = df.drop_duplicates(subset = ['record_date','participant_name'])
    screen_input = df.pivot(index = 'record_date', columns = 'participant_name', values = 'percent').fillna(0)
    filter_result = stock_filter(screen_input)
    if any(filter_result):
        backtest_list.append([stock, filter_result.index[filter_result].tolist()])
    


########################################

import backtrader as bt
import datetime as datetime
import yfinance as yf
import backtrader.analyzers as btanalyzers
from backtrader.analyzers import SharpeRatio

#####################################
##############################        
start_date = datetime.date(2022, 3, 8)
end_date = datetime.date(2022,4,8)
class MyStrategy(bt.Strategy):

    params = (
            ('exitbars',5),
        )    
    def __init__(self):
        self.bar_executed = {key: 0 for key in range(len(backtest_list))}
        
    
    def next(self):
        i=0
        for ticker, backtest_dates in backtest_list:
            cur_date = self.data.datetime.date()
            #cur_date = datetime.datetime.strptime(str(cur_date),"%Y-%m-%d")
            
            #print(cur_date)
            if cur_date in backtest_dates:
                self.log("Buy Create {}".format(self.datas[i]))
                self.buy(self.datas[i])
                self.bar_executed[i] = len(self)
                print(len(self), i, len(self.datas[i]),ticker, cur_date, backtest_dates)
            
            
            if self.bar_executed[i]>0:
                if len(self) >= (self.bar_executed[i] +self.params.exitbars):
                    self.log("Sell create {}".format(self.datas[i]))
                    self.sell(self.datas[i])
                    self.bar_executed[i]=0
                    print(len(self), i, len(self.datas[i]),ticker, cur_date, backtest_dates)
            i+=1
            
            
    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print("{} {}".format(dt.isoformat(),txt))
############################
cerebro = bt.Cerebro()


if backtest_list:
    for ticker,backtest_dates in backtest_list:
        temp = bt.feeds.PandasData(dataname=yf.download(str(int(ticker)).zfill(4)+'.HK', start_date, end_date, auto_adjust=True))
        cerebro.adddata(temp)
    
    
cerebro.addsizer(bt.sizers.SizerFix, stake=20)
cerebro.addstrategy(MyStrategy)
cerebro.addanalyzer(SharpeRatio, _name='mysharpe')
cerebro.addanalyzer(bt.analyzers.DrawDown)
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)
cerebro.addanalyzer(bt.analyzers.SharpeRatio)
cerebro.broker.setcash(1000000)
cerebro.broker.setcommission(commission = 0.001)
print("Start portfolio {}".format(cerebro.broker.getvalue()))
thestrats = cerebro.run()

print("FInal Portfolio {}".format(cerebro.broker.getvalue()))
thestrat = thestrats[0]
#print(thestrat.analyzers.mysharpe.get_analysis())
for each in thestrat.analyzers:
    each.print()

#cerebro.plot()



######################################