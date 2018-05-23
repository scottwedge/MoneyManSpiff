"""
Get historical data from Poloniex, based on a pairs file that contains a CSV file of currency pairs
Example: "BTC_ETH,BTC_STRAT,BTC_ETC"

Gets 5 minute (300 second) candles (finest resolution supported by Poloniex) other supported intervals are 900, 1800, 7200, 14400, and 86400
Poloniex API: https://poloniex.com/support/api/



Based off of work done by jyunfan, modified by Parker Timmerman (parkmycar)
"""
import os
import sys
import time
import pandas as pd


FETCH_URL = "https://poloniex.com/public?command=returnChartData&currencyPair=%s&start=%d&end=%d&period=300"
#PAIR_LIST = ["BTC_ETH"]
DATA_DIR = "data"
COLUMNS = ["date","high","low","open","close","volume","quoteVolume","weightedAverage"]

def get_data(pair):
    datafile = os.path.join(DATA_DIR, pair+".csv")
    timefile = os.path.join(DATA_DIR, pair)

    # If we already have data for a pair, start at the latest data we fetched
    if os.path.exists(datafile):
        newfile = False
        start_time = int(open(timefile).readline()) + 1
        #print("{0:10} : {1}Data already gotten, skipping to currency pair for which no data exists!{2}".format(pair,'\033[93m', '\033[0m'))
        #return
    else:
        newfile = True
        start_time = 1388534400     # 2014.01.01
    end_time = 9999999999#start_time + 86400*30

    url = FETCH_URL % (pair, start_time, end_time)
    print("URL: ", url)
    print("Get %s from %d to %d" % (pair, start_time, end_time))

    df = pd.read_json(url, convert_dates=False)

    #import pdb;pdb.set_trace()

    if df["date"].iloc[-1] == 0:
        print("{}No data.{}".format('\033[93m', '\033[0m'))
        return

    end_time = df["date"].iloc[-1]
    ft = open(timefile,"w")
    ft.write("%d\n" % end_time)
    ft.close()
    outf = open(datafile, "a")
    if newfile:
        df.to_csv(outf, index=False, columns=COLUMNS)
    else:
        df.to_csv(outf, index=False, columns=COLUMNS, header=False)
    outf.close()
    print("{0}Finish.{1}".format('\033[92m', '\033[0m'))
    time.sleep(60)     # Sleep for 60 seconds to prevent spamming the public API server (lowering this could cause an HTTP 500 error)


def main():
    # 1. Check to make sure currency pair file is given
    if (len(sys.argv)) != 2:
        print("Need to provide one argument, the CSV file of currency pairs!")
        sys.exit(0)

    # 2. Read given currency pairs file
    print("Currency pairs for data to be fetched: ")
    cp_df = pd.read_csv(sys.argv[1])
    given_pairs = [pair for pair in cp_df.columns]
    
    # 3. Get all current supported pairs from Poloniex
    df = pd.read_json("https://poloniex.com/public?command=return24hVolume")
    valid_btc_pairs = [pair for pair in df.columns if pair.startswith('BTC')]
    
    # 4. Make sure each given pair is valid
    for pair in given_pairs:
        if pair not in valid_btc_pairs:
            given_pairs.remove(pair)
            print("\t{0:10} : {1}INVALID (removed){2}".format(pair,'\033[91m','\033[0m'))
        else:
            print("\t{0:10} : {1}VALID{2}".format(pair, '\033[92m', '\033[0m'))
    
    # 5. If a "data" directory does not exist, create it
    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)

    # 6. Fetch data from Poloniex for each pair
    for pair in given_pairs:
        get_data(pair)
        time.sleep(2)

if __name__ == '__main__':
    main()
