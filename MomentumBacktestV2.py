from datetime import datetime, timedelta, date
import pandas as pd
import time
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress
import os.path
from tiingo import TiingoClient
import sys
import urllib.request as request
import csv
#from urllib.parse import urlencode
#%matplotlib inline
#plt.rcParams["figure.figsize"] = (10, 6) # (w, h)
#plt.ioff()
#import pandas_datareader.data as web
#from pandas_datareader import data, wb
#import pandas.io.data as web1  # Package and modules for importing data; this code may change depending on pandas version
#import requests
#from bs4 import BeautifulSoup
#import json
#import re
def tiingo_data(ticker, start, end):

    config = {}
    # To reuse the same HTTP Session across API calls (and have better performance), include a session key.
    config['session'] = True
    # Obtain Tiingo API Key
    myFile = open("/Users/brittanythomas/PycharmProjects/SystemTraderV2/tiingoAPIkey.txt", "r")
    myAPIkey = myFile.readline()
    myFile.close()
    config['api_key'] = myAPIkey
    # Initialize
    client = TiingoClient(config)

    try:
        print('Trying to pull Tiingo data for '+ticker)
        df = client.get_dataframe(ticker,
                    startDate=start,
                    endDate=end,
                    frequency='daily')
    except:
        print("Unexpected error:", sys.exc_info()[0])
        time.sleep(1)
        try:
            print('AGAIN - Trying to pull Tiingo data for ' + ticker)
            df = client.get_dataframe(ticker,
                       startDate=start,
                       endDate=end,
                       frequency='daily')
        except:
            print('Could not pull Tiingo data for ' + ticker)
            print("Unexpected error:", sys.exc_info()[0])
            return None
    return df

def momentum(closes):
    returns = np.log(closes)
    x = np.arange(len(returns))
    slope, _, rvalue, _, _ = linregress(x, returns)
    return ((1 + slope) ** 252) * (rvalue ** 2)  # annualize slope and multiply by R^2

def main():
    #Define system file path for where you have stored the constituents.csv and WIKI_PRICES.csv
    sysFiles1 = '/Users/brittanythomas/PycharmProjects/SystemTraderV2/'
    #Define system file path where momentum results should be stored
    sysFiles2='/Users/brittanythomas/Library/Application Support/JetBrains/PyCharmCE2020.1/scratches/datas/'
    #Open a txt file to save troubleshooting data as necessary
    troubleshootFile1 =  open(sysFiles1+'troubleshooting.txt','w+')
    troubleshootFile1.write('test'+'\n')

    skiped =[]
    mydateparser = lambda x: datetime.strptime(x, "%Y-%m-%d")
    constituents = pd.read_csv(sysFiles1 + 'constituents.csv', header=0,
                               names=['date_column', 'tickers'], parse_dates=['date_column'], date_parser=mydateparser)

    #create a list of constituents from constituent.csv dataframe
    conList = set([a for b in constituents.tickers.str.strip('[]').str.split(',') for a in b])
    conList = [s.replace("'",'') for s in conList] #remove quotes from strings in list
    conList = [s.strip() for s in conList]
    conList = list(dict.fromkeys(conList)) #remove duplicates by converting conList into a dictionary and then back again
    conList = sorted(conList) #sort conList alphabetically

    start = "2015-10-01"
    end = "2020-09-01"

    momentums = pd.DataFrame(columns=['ticker','momentum'])

    i=0
    for ticker in conList:
        if os.path.isfile(sysFiles2 + ticker + '.csv'):
            try:
                print(ticker + ' momentum exists - Adding to dictionary')
                df = pd.read_csv(sysFiles2+ticker+'.csv',header='infer', sep=' ')
                momentums = momentums.append({'ticker':ticker, 'momentum':df['momentum'].iloc[-1]}, ignore_index=True)
            except:
                print("Unexpected error:", sys.exc_info()[0])
                skiped.append(ticker)
                i=i+1
                continue
        else:
            print(ticker + ' is not recorded - attempting Tiingo')
            df = tiingo_data(ticker, start, end)
            if df is None:
                print(ticker + ' was not available on Tiingo')
                skiped.append(ticker)
                i = i + 1
                continue
            else:
                print(ticker + ' is being added to the momentums dataframe - calculating momentum')
                df.insert(12,"momentum",df['close'].rolling(90).apply(momentum))
                df.to_csv(r'' + sysFiles2 + ticker + '.csv', sep=' ')
                momentums = momentums.append({'ticker':ticker, 'momentum':df['momentum'].iloc[-1]}, ignore_index=True)
                i = i + 1

    print(momentums)
    print(skiped)

    #set rotation interval in days
    rotationInterval = 30
    #set beginning investment amount
    begInvestment = 50000
    #set number of investments
    numInvest = 10
    #advancements could include:
    #   A % invested in VXX, Cash, etc
    #   Variable % invested vs not-invested due to high valuations or some other market criteria
    #   Additional selection criteria on top of momentum

    #Loop through data and purchase top numInvest every rotationInterval
    #Need to keep track of investableCash and show profit and ROI at the end (in TWA terms)

    #For comparison, purchase begInvestment of SPY and compare to strategy above

    troubleshootFile1.close()

if __name__ == "__main__":
    main()