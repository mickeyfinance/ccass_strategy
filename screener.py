#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 17:27:44 2023

@author: mickeylau
"""


#import mysql.connector
import pandas as pd

##############
def stock_filter(df, broker_holding_change, concentration_crit):
    broker_change = pd.DataFrame()
    for column in df.columns[0:-3]:
        broker_change['{}_change'.format(column)]= df[column].diff().fillna(0)
    
    # Criteria 1: check if broker got a big change in holdings 
    Criteria1 = (abs(broker_change) > broker_holding_change)
    df["Criteria1"] = Criteria1.any(axis='columns')
    

    # Criteria 2: check if retail type broker decreases   
    df['Criteria2'] = ((df['Retail'].diff())<df['unknown'].diff())

    # Criteria 3: concentration - top 5 brokers occupy a certain percentage in ccass
    df['Criteria3'] = df.select_dtypes('number').apply(lambda r: r.nlargest(5).sum(), axis=1)>concentration_crit
    
    
    # Check if all criteria are met
    df['Fullfilment'] = df[['Criteria1','Criteria2','Criteria3']].all(axis='columns')
 
    
    return (df['Fullfilment'])
#############


"""
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="xxxxxx",
  database="ccass_data"
)
mycursor = mydb.cursor()
stock_list = mycursor.execute("SELECT DISTINCT stock_code FROM holdings")
stock_list = mycursor.fetchall()
"""
##########
