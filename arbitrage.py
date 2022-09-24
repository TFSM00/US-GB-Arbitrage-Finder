from urllib.request import urlopen
import json
from os.path import exists
import datetime as dt
import pathlib
import PySimpleGUI as sg



def updateJSON(API_KEY):
    """Updates the relevant equity data csv files"""

    for i in ["NYSE", "NASDAQ", "LSE"]:
            url = (f"https://financialmodelingprep.com/api/v3/stock-screener?exchange={i}&apikey={API_KEY}")
            data = get_jsonparsed_data(url)
            with open(f"{i}.json", 'w', encoding="UTF-8") as f:
                json.dump(data, f)

    
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
    #* Also checks if the json files are up to date
    if exists("NYSE.json") and exists("NASDAQ.json") and exists("LSE.json"):
        for i in ["NYSE.json", "NASDAQ.json", "LSE.json"]:
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
                updateJSON(API_KEY)
    else:
        updateJSON(API_KEY)
    #* ================================================

    #* Grabs info from csv into dataframes
    NY, NAS, GB = "", "", ""
    with open("NYSE.json", encoding="UTF-8") as f_ny:
        NY = json.load(f_ny)
    with open("NASDAQ.json", encoding="UTF-8") as f_nas:
        NAS = json.load(f_nas)
    with open("LSE.json", encoding="UTF-8") as f_ny:
        GB = json.load(f_ny)
    #* ===================================

    #* Removes not actively trading equities
    for exchange in [NY, NAS, GB]:
        for stock in exchange:
            if stock.get("isActivelyTrading") == "false" or int(stock.get("marketCap")) == 0 or float(stock.get("price")) == 0.0:
                exchange.remove(stock)
    #* ========================================
    
    NY_companies = [stock.get("companyName") for stock in NY]
    GB_companies = [stock.get("companyName") for stock in GB]
    NAS_companies = [stock.get("companyName") for stock in NAS]
    commonNYGB = []
    commonNASGB = []

    #* Grabs Multi-Listed Companies
    for stock in GB_companies:
        if stock in NY_companies:
            commonNYGB.append(stock)
        elif stock in NAS_companies:
            commonNASGB.append(stock)

    #* ============================

    #* Gets the price of the stock
    arbiNYGB = []

    for stock in commonNYGB:
        no_error = False
        try:
            usd = [float(i.get("price")) for i in NY if i.get("companyName") == stock][0]
            gbp = [float(i.get("price")) for i in GB if i.get("companyName") == stock][0]
            no_error = True
        except IndexError:
            continue
        if no_error:
            if float(usd) != 0.0 and float(gbp) != 0.0:
                arbiNYGB.append({stock: [usd, gbp]})

    print(arbiNYGB)
    arbiNASGB = []

    for i in commonNASGB:
        no_error = False
        try:
            usd = [float(i.get("price")) for i in NAS if i.get("companyName") == stock][0]
            gbp = [float(i.get("price")) for i in GB if i.get("companyName") == stock][0]
            no_error = True
        except IndexError:
            continue
        if no_error:
            if float(usd) != 0.0 and float(gbp) != 0.0:
                arbiNASGB.append({stock: [usd, gbp]})


    arbitrageList_prov = arbiNYGB + arbiNASGB
    arbitrageList = []
    duplicate_remove = [arbitrageList.append(x) for x in arbitrageList_prov if x not in arbitrageList]
    #* ===================================================================

    #* Grabs the stocks with near equivalent prices in both exchanges
    arbitrage = []

    for i in arbitrageList:
        prices = list(i.values())[0]
        if abs((prices[0]/prices[1]) - 1) < 0.10:
            if prices[0] > prices[1]:
                arbitrage.append([list(i.keys())[0], "GB", "US", round((prices[0]-prices[1]),7)])
            elif prices[1] > prices[0]:
                arbitrage.append([list(i.keys())[0], "US", "GB", round((prices[1]-prices[0]),7)])
    #* ==============================================================


    return arbitrage

if __name__=="__main__":
    def open_window(key):
        table = GB_US_Arbitrage(key)
        headings = ["Company Name", "Buy Side", "Sell Side", "Arbitrage per Share (in USD)"]
        data = table
        print(data)

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

        window = sg.Window("US-GB Arbitrage Opportunity Finder", layout,)
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



    
    







