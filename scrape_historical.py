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
from selenium.webdriver.common.by import By
import mysql.connector



mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="91692388",
  database="ccass_data"
)

mycursor = mydb.cursor()
##############

df = pd.read_excel('/Users/mickeylau/Desktop/Big project/ListOfSecurities.xlsx', usecols=[0], skiprows=2)
stock_codes = df['Stock Code'].astype(str).str.zfill(5).tolist()

trading_dates = pd.read_excel('/Users/mickeylau/Desktop/Big project/ListOfSecurities.xlsx', sheet_name="2022trading_dates")
time_interval = 24 * 60 * 60  # 24 hours in seconds
##############

def scrape_ccass(stock_code,trading_date):

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    # navigate to the website
    driver.get("https://www3.hkexnews.hk/sdw/search/searchsdw.aspx")

    # find the stock code input field
    stock_code_input = driver.find_element("id","txtStockCode")

    stock_code_input.send_keys(stock_code)

    ##########
    
    
    date_input = driver.find_element("id","txtShareholdingDate")
    
    date_input.click()
    
    #driver.implicitly_wait(1)
    
    ########
    dt = datetime.strptime(trading_date, '%Y/%m/%d')
    
    select_year = driver.find_element(By.XPATH,"//b[@class='year']//button[@data-value={}]".format(dt.year)).click()
    select_day = driver.find_element(By.XPATH,"//b[@class='day']//button[@data-value={}]".format(dt.day)).click()
    real_month=dt.month-1
    select_month = driver.find_element(By.XPATH,"//b[@class='month']//button[@data-value={}]".format(real_month)).click()
    
    driver.find_element(By.XPATH,"//body").click()
    #########
    # find the search button and click it
    search_button = driver.find_element("id","btnSearch")
    search_button.click()
    
    shareholding_date=driver.find_element("id","txtShareholdingDate").get_attribute('value')
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
    temp['record_date']=shareholding_date
    temp['stock_code']=stock_code
    
    driver.close()
    
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
    
    for date in trading_dates['Trading Date']:
        for stock_code in stock_codes:
            try:
                scrape_ccass(stock_code,date)
            except:
                pass
            print(stock_code,date)
        
    #time.sleep(time_interval)   
###########

