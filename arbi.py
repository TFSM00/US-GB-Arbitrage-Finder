import pandas as pd
import pandas_datareader as pdr
from urllib.request import urlopen
import json

API_KEY = "2216ee6199f3f54f8c720b9eee1ea5f1"

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

def GB_US_Arbitrage():
    for i in ["NYSE", "NASDAQ", "LSE"]:
        url = ("https://financialmodelingprep.com/api/v3/stock-screener?limit=100&exchange=NASDAQ&country=GB&apikey=2216ee6199f3f54f8c720b9eee1ea5f1")
        data = get_jsonparsed_data(url)

        df = pd.DataFrame(data)
        df.to_csv(f"{i}.csv")

    NY = pd.read_csv("NYSE.csv")
    NAS = pd.read_csv("NASDAQ.csv")
    GB = pd.read_csv("LSE.csv")

    exchangeRate = pdr.get_data_yahoo("GBPUSD=X")["Adj Close"][-1]

    companies = [NY["companyName"], NAS["companyName"], GB["companyName"]]

    NY.set_index("companyName",inplace=True)
    NAS.set_index("companyName",inplace=True)
    GB.set_index("companyName",inplace=True)

    commonNYGB = []
    commonNASGB = []

    for i in list(GB.index):
        if i in list(NY.index):
            commonNYGB.append(i)
        elif i in list(NAS.index):
            commonNASGB.append(i)

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
    equalSharePower = []

    for i in arbitrageList:
        prices = list(i.values())[0]
        if abs((prices[0]/prices[1]) - 1) < 0.1:
            if prices[0] > prices[1]:
                equalSharePower.append([list(i.keys())[0], "GB", "US", abs((prices[0]/prices[1]) - 1)])
            elif prices[1] > prices[0]:
                equalSharePower.append([list(i.keys())[0], "US", "GB", abs((prices[0]/prices[1]) - 1)])


    arbitrage = pd.DataFrame(equalSharePower, columns=["Company Name", "Buy Side", "Sell Side", "Arbitrage (in USD)"])
    return arbitrage


if __name__=="__main__":
    print(GB_US_Arbitrage())






