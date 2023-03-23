#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 17:27:44 2023

@author: mickeylau
"""

import pytest
import pandas as pd
import os
import datetime as datetime
from screener import stock_filter

def test_stock_filter():
    
    
    test_df = pd.read_csv(os.getcwd()+'/data/test_stock_filter.csv', index_col='record_date')
    test_result = ['2022-03-09', '2022-03-10', '2022-03-11', '2022-03-15']   
    filter_result = stock_filter(test_df)
    assert filter_result.index[filter_result].tolist() == test_result

