# Imports, of course
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import time

import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="91692388",
  database="ccass_data"
)

mycursor = mydb.cursor()
###########

snapshot_dict ={}
# Load the stock codes from the Excel file
df = pd.read_excel('/Users/mickeylau/Desktop/Big project/ListOfSecurities.xlsx', usecols=[0], skiprows=2)
stock_codes = df['Stock Code'].astype(str).str.zfill(5).tolist()

# Set the time interval (in seconds) for running the script daily
time_interval = 24 * 60 * 60  # 24 hours in seconds


def scrape_ccass(stock_code):
    # Initialize a Firefox webdriver
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    # navigate to the website
    driver.get("https://www3.hkexnews.hk/sdw/search/searchsdw.aspx")
    
    # find the stock code input field
    stock_code_input = driver.find_element("id","txtStockCode")
    
    # enter "1" in the stock code input field
    stock_code_input.send_keys(stock_code)
    
    # find the search button and click it
    search_button = driver.find_element("id","btnSearch")
    search_button.click()
    
    driver.page_source
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    
    ########
    table= soup.find('tbody')
    tr = table.find_all('tr')
    
    participant_id=[]
    participant_name=[]
    address =[]
    shareholding=[]
    percent=[]
    
    for el in tr:
        participant_id.append(el.find('td', {'class': 'col-participant-id'}).find('div',{'class':'mobile-list-body'}).text.strip())
        participant_name.append(el.find('td', {'class': 'col-participant-name'}).find('div',{'class':'mobile-list-body'}).text.strip())
        address.append(el.find('td', {'class': 'col-address'}).find('div',{'class':'mobile-list-body'}).text.strip())
        shareholding.append(el.find('td', {'class': 'col-shareholding'}).find('div',{'class':'mobile-list-body'}).text.strip())
        percent.append(el.find('td', {'class': 'col-shareholding-percent'}).find('div',{'class':'mobile-list-body'}).text.strip())
    
    temp = pd.DataFrame()

    temp['participant_id']= participant_id
    temp['participant_name']= participant_name
    temp['address']= address
    temp['shareholding']= shareholding
    temp['shareholding'] = temp['shareholding'].str.replace(",","").astype('int')
    temp['percent']= percent
    temp['percent']= temp['percent'].str.rstrip("%").astype(float)/100
    temp['record_date']=datetime.now().strftime("%Y%m%d")
    temp['stock_code']=stock_code
    
    # insert to database
    cols = "`,`".join([str(x) for x in temp.columns.tolist()])

    for i,row in temp.iterrows():
        sql = "INSERT INTO `holdings` (`" +cols + "`) VALUES (" + "%s,"*(len(row)-1) + "%s)"
        mycursor.execute(sql, tuple(row))

        # the connection is not autocommitted by default, so we must commit to save our changes
        mydb.commit()
    
    """
    if stock_code in snapshot_dict:
        snapshot_dict[stock_code].append(temp)
    else:
        snapshot_dict[stock_code]=temp
    """

if __name__ == "__main__":
    for stock_code in stock_codes:
        scrape_ccass(stock_code)
        
    time.sleep(time_interval)   
###########

