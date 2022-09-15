from urllib.request import urlopen
import json
from os.path import exists
import datetime as dt
import pathlib

import pandas as pd
import yfinance as yf
import PySimpleGUI as sg

def updateCSVS(API_KEY):
    """Updates the relevant equity data csv files"""

    for i in ["NYSE", "NASDAQ", "LSE"]:
            url = (f"https://financialmodelingprep.com/api/v3/stock-screener?limit=100&exchange={i}&country=GB&apikey={API_KEY}")
            data = get_jsonparsed_data(url)

            df = pd.DataFrame(data)
            df.to_csv(f"{i}.csv")

def get_jsonparsed_data(url):
    """
    Receive the content of ``url``, parse it as JSON and return the object.

    Parameters
    ----------
    url : str

    Returns
    -------
    dict
    """
    response = urlopen(url)
    data = response.read().decode("utf-8")
    return json.loads(data)

def GB_US_Arbitrage(API_KEY):

    #* Checks if there are already tables to avoid unnecessary request for the API
    #* Also checks if the CSV files are up to date
    if exists("NYSE.csv") and exists("NASDAQ.csv") and exists("LSE.csv"):
        for i in ["NYSE.csv", "NASDAQ.csv", "LSE.csv"]:
            # create a file path
            path = pathlib.Path(i)
            
            # get modification time
            timestamp = path.stat().st_mtime
            
            # convert time to dd-mm-yyyy hh:mm:ss
            modifDate = dt.date.fromtimestamp(timestamp)
            today = dt.date.today()
            if today == modifDate:
                pass
            else:
                for i in ["NYSE", "NASDAQ", "LSE"]:
                    url = (f"https://financialmodelingprep.com/api/v3/stock-screener?limit=100&exchange={i}&country=GB&apikey={API_KEY}")
                    data = get_jsonparsed_data(url)

                    df = pd.DataFrame(data)
                    df.to_csv(f"{i}.csv")
    else:
        for i in ["NYSE", "NASDAQ", "LSE"]:
            url = (f"https://financialmodelingprep.com/api/v3/stock-screener?limit=100&exchange={i}&country=GB&apikey={API_KEY}")
            data = get_jsonparsed_data(url)

            df = pd.DataFrame(data)
            df.to_csv(f"{i}.csv")
    #* ================================================

    #* Grabs info from csv into dataframes
    NY = pd.read_csv("NYSE.csv")
    NAS = pd.read_csv("NASDAQ.csv")
    GB = pd.read_csv("LSE.csv")
    #* ===================================

    #* Obtains real-time GBPUSD quote
    exchangeRate = float(yf.download(tickers = "GBPUSD=X" ,period ='1d', interval = '15m', progress=False)["Adj Close"][-1])
    #* ==============================

    #* Makes companyName the index for easier access to rows
    NY.set_index("companyName",inplace=True)
    NAS.set_index("companyName",inplace=True)
    GB.set_index("companyName",inplace=True)

    #* =====================================================

    #* Removes not actively trading equities
    NY = NY[NY.isActivelyTrading != False]
    NAS = NAS[NAS.isActivelyTrading != False]
    GB = GB[GB.isActivelyTrading != False]

    #* ========================================

    commonNYGB = []
    commonNASGB = []

    #* Grabs Multi-Listed Companies
    for i in list(GB.index):
        if i in list(NY.index):
            commonNYGB.append(i)
        elif i in list(NAS.index):
            commonNASGB.append(i)

    commonNYGB = set(commonNYGB)
    commonNASGB = set(commonNASGB)
    #* ============================

    #* Gets the price of the stock and its equivalent in the other exchange
    arbiNYGB = []

    for i in commonNYGB:
        usd = NY.loc[i]["price"]
        gbp = GB.loc[i]["price"]
        gbpEquiv = (gbp/100) * exchangeRate
        arbiNYGB.append({i: [usd, gbpEquiv]})

    arbiNASGB = []

    for i in commonNASGB:
        usd = NAS.loc[i]["price"]
        gbp = GB.loc[i]["price"]
        gbpEquiv = (gbp/100) * exchangeRate
        arbiNASGB.append({i: [usd, gbpEquiv]})

    #! BEWARE: YAHOO DATA IN GBp (0.01GBP) - that's why it is div. by 100

    arbitrageList = arbiNYGB + arbiNASGB
    #* ===================================================================

    #* Grabs the stocks with near equivalent prices in both exchanges
    equalSharePower = []

    for i in arbitrageList:
        prices = list(i.values())[0]
        if abs((prices[0]/prices[1]) - 1) < 0.10:
            if prices[0] > prices[1]:
                equalSharePower.append([list(i.keys())[0], "GB", "US", round(abs((prices[0]/prices[1]) - 1),7)])
            elif prices[1] > prices[0]:
                equalSharePower.append([list(i.keys())[0], "US", "GB", round(abs((prices[0]/prices[1]) - 1),7)])
    #* ==============================================================


    arbitrage = pd.DataFrame(equalSharePower, columns=["Company Name", "Buy Side", "Sell Side", "Arbitrage per Share (in USD)"])
    return arbitrage


if __name__=="__main__":
    def open_window(key):
        table = GB_US_Arbitrage(key)
        headings = list(table.columns)
        data = table.values.tolist()

        layout = [[sg.Table(data, headings=headings, justification="left", key="-TABLE-", max_col_width=30, font=('Any 13'))]] 
        window = sg.Window("US-GB Arbitrage Opportunity Finder", layout, modal=False)
        choice = None
        while True:
            event, values = window.read()
            if event == "Exit" or event == sg.WIN_CLOSED:
                break
            
        window.close()
    
    def main():
        layout = [[sg.Text('Enter your API Key Here: ', font=('Any 13'))],      
                 [sg.InputText(key='key', font=('Any 13'))],      
                 [sg.Submit(key="submit", font=('Any 13')), sg.Cancel(font=('Any 13'))]]  

        window = sg.Window("US-GB Arbitrage Opportunity Finder", layout)
        while True:
            event, values = window.read()

            if event == "Exit" or event == sg.WIN_CLOSED:
                break
            if event == "submit":
                key = str(values["key"])
                open_window(key)
                window.close()
        
        window.close()

    main()



    
    







